# -*- mode: python; coding: utf-8 -*-
import logging
import re
import sys
import os
from traceback import *
from drydrop_handler import DEVELOPMENT_PROJECT_ROOT

# generate nice traceback with optional textmate links
def format_nice_traceback(traceback):
    tb = "<table>"
    lines = traceback.splitlines(1)
    lines.reverse()
    for line in lines[1:len(lines)-2]:
        filename = re.findall('File "(.+)",', line)
        linenumber = re.findall(', line\s(\d+)', line)
        modulename = re.findall(', in ([A-Za-z0-9_]+)', line)
        if filename and linenumber and not re.match("<(.+)>",filename[0]):
            file_name = filename[0]
            # tohle je preklad cesty z google masiny na lokalni vyvojovy stroj
            m = re.match(r"^/base/data/home/.*/[0-9]*-[0-9a-f]*\.[0-9]*/(.*)$", file_name)
            if m: 
                file_name = DEVELOPMENT_PROJECT_ROOT+m.group(1)
            else:
                m = re.match(r"^.*?\.zip/(.*)$", file_name)
                if m: file_name = DEVELOPMENT_PROJECT_ROOT+m.group(1)
            module_name = 'in <span class="module">%s</span>' % modulename[0] if modulename else ""
            base_name = os.path.basename(file_name)
            line = linenumber[0]
            html = '<tr><td><a class="file" href="txmt://open/?url=file://%s&line=%s">%s:%s</a></td><td>%s</td></tr>\n' % (file_name,line,base_name,line,module_name)
            tb += html
    tb += '</table>'
    return tb

def show_error(handler, code, log_msg = ''):
    handler.error(code)
    handler.response.out.write('<html><body>')
    if sys.exc_info()[0]:
        if not isinstance(sys.exc_info()[0], str):
            exception_name = sys.exc_info()[0].__name__
            exception_details = str(sys.exc_info()[1])
        else:
            exception_name = 'Exception'
            exception_details = str(sys.exc_info())
        exception_traceback = ''.join(format_exception(*sys.exc_info()))
            
        # logging.error(exception_name)
        # logging.error(exception_details)
        # logging.error(log_msg)
        # logging.error(exception_traceback)

        tb=format_nice_traceback(exception_traceback)
        handler.response.out.write('<html><body><head><title>'+exception_details+'</title>\n')
        handler.response.out.write('<style>\n')
        handler.response.out.write('html {font-family: arial}\n')
        handler.response.out.write('h1 { padding:5px; color: white; background-color:red; font-weight:bold;}\n')
        handler.response.out.write('h2 { padding-bottom: 0px; margin-bottom: 0px; }\n')
        handler.response.out.write('.file { font-family: courier; font-size: 12px; }\n')
        handler.response.out.write('.module { color: darkGreen; }\n')
        handler.response.out.write('</style></head>\n')
        handler.response.out.write('<h1>%s: %s</h1>\n' % (exception_name, exception_details))
        handler.response.out.write('<h2>Traceback:</h2>\n')
        handler.response.out.write('%s' % tb)
    else:
        handler.response.out.write('<h1>%s</h1>\n' % log_msg)
    handler.response.out.write('<script>var a = document.getElementsByTagName("a")[0]; if (a) window.open(a.href, "_self");</script>')
    handler.response.out.write('</body></html>')

# toto je dekorator
def nice_traceback(f):
    def inner(self, *args, **kvargs):
        try:
            f(self, *args, **kvargs)
        except:
            show_error(self, 500)
    return inner
