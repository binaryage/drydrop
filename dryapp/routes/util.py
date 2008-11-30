"""Utility functions for use in templates / controllers

*PLEASE NOTE*: Many of these functions expect an initialized RequestConfig
object. This is expected to have been initialized for EACH REQUEST by the web
framework.

"""
import os
import re
import urllib
from routes import request_config

def _screenargs(kargs):
    """
    Private function that takes a dict, and screens it against the current 
    request dict to determine what the dict should look like that is used. 
    This is responsible for the requests "memory" of the current.
    """
    config = request_config()
    
    # Coerce any unicode args with the encoding
    encoding = config.mapper.encoding
    for key, val in kargs.iteritems():
        if isinstance(val, unicode):
            kargs[key] = val.encode(encoding)
    
    if config.mapper.explicit and config.mapper.sub_domains:
        return _subdomain_check(config, kargs)
    elif config.mapper.explicit:
        return kargs
    
    controller_name = kargs.get('controller')
    
    if controller_name and controller_name.startswith('/'):
        # If the controller name starts with '/', ignore route memory
        kargs['controller'] = kargs['controller'][1:]
        return kargs
    elif controller_name and not kargs.has_key('action'):
        # Fill in an action if we don't have one, but have a controller
        kargs['action'] = 'index'
    
    memory_kargs = getattr(config, 'mapper_dict', {}).copy()
    
    # Remove keys from memory and kargs if kargs has them as None
    for key in [key for key in kargs.keys() if kargs[key] is None]:
        del kargs[key]
        if memory_kargs.has_key(key):
            del memory_kargs[key]
    
    # Merge the new args on top of the memory args
    memory_kargs.update(kargs)
    
    # Setup a sub-domain if applicable
    if config.mapper.sub_domains:
        memory_kargs = _subdomain_check(config, memory_kargs)
    
    return memory_kargs

def _subdomain_check(config, kargs):
    """Screen the kargs for a subdomain and alter it appropriately depending
    on the current subdomain or lack therof."""
    if config.mapper.sub_domains:
        subdomain = kargs.pop('sub_domain', None)
        if isinstance(subdomain, unicode):
            subdomain = str(subdomain)
        
        # We use a try/except here, cause the only time there should be no
        # environ is when we're unit testing, in which case we shouldn't be
        # changing kargs and such. The exception catching also won't hurt as
        # badly here vs doing a hasattr on every url check
        try:
            fullhost = config.environ.get('HTTP_HOST') or \
                config.environ.get('SERVER_NAME')
        except AttributeError:
            return kargs
        
        hostmatch = fullhost.split(':')
        host = hostmatch[0]
        port = ''
        if len(hostmatch) > 1:
            port += ':' + hostmatch[1]
        sub_match = re.compile('^.+?\.(%s)$' % config.mapper.domain_match)
        domain = re.sub(sub_match, r'\1', host)
        if subdomain and not host.startswith(subdomain) and \
            subdomain not in config.mapper.sub_domains_ignore:
            kargs['_host'] = subdomain + '.' + domain + port
        elif (subdomain in config.mapper.sub_domains_ignore or \
            subdomain is None) and domain != host:
            kargs['_host'] = domain + port
        return kargs
    else:
        return kargs
    

def _url_quote(string, encoding):
    """A Unicode handling version of urllib.quote."""
    if encoding:
        if isinstance(string, unicode):
            s = string.encode(encoding)
        elif isinstance(string, str):
            # assume the encoding is already correct
            s = string
        else:
            s = unicode(string).encode(encoding)
    else:
        s = str(string)
    return urllib.quote(s, '/')

def url_for(*args, **kargs):
    """Generates a URL 
    
    All keys given to url_for are sent to the Routes Mapper instance for 
    generation except for::
        
        anchor          specified the anchor name to be appened to the path
        host            overrides the default (current) host if provided
        protocol        overrides the default (current) protocol if provided
        qualified       creates the URL with the host/port information as 
                        needed
        
    The URL is generated based on the rest of the keys. When generating a new 
    URL, values will be used from the current request's parameters (if 
    present). The following rules are used to determine when and how to keep 
    the current requests parameters:
    
    * If the controller is present and begins with '/', no defaults are used
    * If the controller is changed, action is set to 'index' unless otherwise 
      specified
    
    For example, if the current request yielded a dict of
    {'controller': 'blog', 'action': 'view', 'id': 2}, with the standard 
    ':controller/:action/:id' route, you'd get the following results::
    
        url_for(id=4)                    =>  '/blog/view/4',
        url_for(controller='/admin')     =>  '/admin',
        url_for(controller='admin')      =>  '/admin/view/2'
        url_for(action='edit')           =>  '/blog/edit/2',
        url_for(action='list', id=None)  =>  '/blog/list'
    
    **Static and Named Routes**
    
    If there is a string present as the first argument, a lookup is done 
    against the named routes table to see if there's any matching routes. The
    keyword defaults used with static routes will be sent in as GET query 
    arg's if a route matches.
    
    If no route by that name is found, the string is assumed to be a raw URL. 
    Should the raw URL begin with ``/`` then appropriate SCRIPT_NAME data will
    be added if present, otherwise the string will be used as the url with 
    keyword args becoming GET query args.
    """
    anchor = kargs.get('anchor')
    host = kargs.get('host')
    protocol = kargs.get('protocol')
    qualified = kargs.pop('qualified', None)
    
    # Remove special words from kargs, convert placeholders
    for key in ['anchor', 'host', 'protocol']:
        if kargs.get(key):
            del kargs[key]
        if kargs.has_key(key+'_'):
            kargs[key] = kargs.pop(key+'_')
    config = request_config()
    route = None
    static = False
    encoding = config.mapper.encoding
    url = ''
    if len(args) > 0:
        route = config.mapper._routenames.get(args[0])
        
        if route and route.defaults.has_key('_static'):
            static = True
            url = route.routepath
        
        # No named route found, assume the argument is a relative path
        if not route:
            static = True
            url = args[0]
        
        if url.startswith('/') and hasattr(config, 'environ') \
                and config.environ.get('SCRIPT_NAME'):
            url = config.environ.get('SCRIPT_NAME') + url
        
        if static:
            if kargs:
                url += '?'
                query_args = []
                for key, val in kargs.iteritems():
                    if isinstance(val, (list, tuple)):
                        for value in val:
                            query_args.append("%s=%s" % (
                                urllib.quote(unicode(key).encode(encoding)),
                                urllib.quote(unicode(value).encode(encoding))))
                    else:
                        query_args.append("%s=%s" % (
                            urllib.quote(unicode(key).encode(encoding)),
                            urllib.quote(unicode(val).encode(encoding))))
                url += '&'.join(query_args)
    if not static:
        route_args = []
        if route:
            if config.mapper.hardcode_names:
                route_args.append(route)
            newargs = route.defaults.copy()
            newargs.update(kargs)
            
            # If this route has a filter, apply it
            if route.filter:
                newargs = route.filter(newargs)
            
            # Handle sub-domains
            newargs = _subdomain_check(config, newargs)
        else:
            newargs = _screenargs(kargs)
        anchor = newargs.pop('_anchor', None) or anchor
        host = newargs.pop('_host', None) or host
        protocol = newargs.pop('_protocol', None) or protocol
        url = config.mapper.generate(*route_args, **newargs)
    if anchor:
        url += '#' + _url_quote(anchor, encoding)
    if host or protocol or qualified:
        if not host and not qualified:
            # Ensure we don't use a specific port, as changing the protocol
            # means that we most likely need a new port
            host = config.host.split(':')[0]
        elif not host:
            host = config.host
        if not protocol:
            protocol = config.protocol
        if url is not None:
            url = protocol + '://' + host + url
    
    if not isinstance(url, str) and url is not None:
        raise RouteException("url_for can only return a string, got "
                        "unicode instead: %s" % url)
    if url is None:
        raise RouteException(
            "url_for could not generate URL. Called with args: %s %s" % \
            (args, kargs))
    return url

def redirect_to(*args, **kargs):
    """Issues a redirect based on the arguments. 
    
    Redirect's *should* occur as a "302 Moved" header, however the web 
    framework may utilize a different method.
    
    All arguments are passed to url_for to retrieve the appropriate URL, then
    the resulting URL it sent to the redirect function as the URL.
    """
    target = url_for(*args, **kargs)
    config = request_config()
    return config.redirect(target)

def controller_scan(directory=None):
    """Scan a directory for python files and use them as controllers"""
    if directory is None:
        return []
    
    def find_controllers(dirname, prefix=''):
        """Locate controllers in a directory"""
        controllers = []
        for fname in os.listdir(dirname):
            filename = os.path.join(dirname, fname)
            if os.path.isfile(filename) and \
                re.match('^[^_]{1,1}.*\.py$', fname):
                controllers.append(prefix + fname[:-3])
            elif os.path.isdir(filename):
                controllers.extend(find_controllers(filename, 
                                                    prefix=prefix+fname+'/'))
        return controllers
    def longest_first(fst, lst):
        """Compare the length of one string to another, shortest goes first"""
        return cmp(len(lst), len(fst))
    controllers = find_controllers(directory)
    controllers.sort(longest_first)
    return controllers

class RouteException(Exception):
    """Tossed during Route exceptions"""
    pass
