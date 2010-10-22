# -*- mode: python; coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from datetime import datetime
import os
import os.path
import sys
import traceback
import logging

APP_ROOT = os.path.normpath(os.path.dirname(__file__))
DRY_ROOT = os.path.join(APP_ROOT, 'drydrop.zip')

LOCAL = os.environ["SERVER_SOFTWARE"].startswith("Development")
APP_ID = os.environ["APPLICATION_ID"]
VER_ID = os.environ["CURRENT_VERSION_ID"]

DEFAULT_CONFIG_SOURCE = """
handlers:
- url: '/'
  static_files: 'index.html index.htm readme.txt readme.markdown readme.md'
  upload: '.*'
- url: '/'
  static_dir: '/'
"""

def routing(m):
  # Routes from http://routes.groovie.org/
  # see the full documentaiton at http://routes.groovie.org/docs/
  # The priority is based upon order of creation: first created -> highest priority.
  
  # Connect the root of your app "http://yourapp.appspot.com/" to a controller/action
  # m.connect('home', '', controller='blog', action='index')
  # use in your application with url_for('home')
  
  # Named Routes
  # Routes can be named for easier use in your controllers/views
  # m.connect( 'history' , 'archives/by_eon/:century', controller='archives', action='show')
  # 
  # use with url_for('history', '1800') 
  # will route to ArchivesController.show() with self.params['century'] equal to '1800'
  
  # Typical route example.
  # m.connect('archives/:year/:month/:day', controller='archives', action='show')
  # 
  # routes urls like archives/2008/12/10 to
  # ArchivesController.show() with self.params['year'], self.params['month'], self.params['day'] available
  # 
  # use in your aplication views/controllers with url_for(controller='archives', year='2008', month='12', day='10')
  
  
  # Connect entire RESTful Resource routing with mapping
  # m.resource('message','messages') 
  # will be a shortcut for the following pattern of routes:
  # GET    /messages         -> MessagesController.index()          -> url_for('messages')
  # POST   /messages         -> MessagesController.create()         -> url_for('messages')
  # GET    /messages/new     -> MessagesController.new()            -> url_for('new_message')
  # PUT    /messages/1       -> MessagesController.update(id)       -> url_for('message', id=1)
  # DELETE /messages/1       -> MessagesController.delete(id)       -> url_for('message', id=1)
  # GET    /messages/1       -> MessagesController.show(id)         -> url_for('message', id=1)
  # GET    /messages/1;edit  -> MessagesController.edit(id)         -> url_for('edit_message', id=1)
  #
  # see http://routes.groovie.org/class-routes.base.Mapper.html#resource for all options
  
  m.connect('/drydrop-static/*path', controller="static", action="static")
  m.connect('/admin/:action', controller="admin", action="index")
  m.connect('/hook/:action', controller="hook", action="index")
  m.connect('/', controller="welcome", action="index")
  
  # returns the mapper object. Do not remove.
  return m
  
def ReadDataFile(path, vfs):
    import httplib
    import logging
    # try:
    resource = vfs.get_resource(path)
    # except:
    #     logging.error('Unable to retrieve file "%s"', path)
    #     return httplib.NOT_FOUND, ""
        
    if resource.content is None:
        logging.warning('Missing file "%s"', path)
        return httplib.NOT_FOUND, "", datetime.now()
        
    # Return the content and timestamp
    return httplib.OK, resource.content, resource.created_on

class AppHandler(webapp.RequestHandler):
    
    def __init__(self):
        import glob
        import os.path
        import routes

        # create a new routing mapper
        self.mapper = routing(routes.Mapper())

        # routes needs to know all the controllers to generate the regular expressions.
        # controllers = []
        # for file in glob.glob(os.path.join(DRY_ROOT, 'app', 'controllers', '*.py')):
        #     name = os.path.basename(file).replace('.py', '')
        #     if not name.startswith('_'):
        #         controllers.append(name)
        # self.mapper.create_regs(controllers)
    
    def get_base_controller(self):
        from drydrop.app.core.controller import BaseController
        return BaseController(self.request, self.response, self)
    
    def meta_dispatch(self, root, config_source, request_path, request_headers, request_environ):
        from drydrop.app.meta.server import ParseAppConfig, MatcherDispatcher, RewriteResponse, cStringIO
        import string
        import logging
        
        HTTP_date = ''

        logging.debug("Meta: dispatching %s", request_path)
        
        login_url = "/login" # TODO
        config, matcher = ParseAppConfig(self.settings.source, config_source, self.vfs, static_caching=True)
        dispatcher = MatcherDispatcher(login_url, [matcher])

        infile = cStringIO.StringIO()
        outfile = cStringIO.StringIO()
        dispatcher.Dispatch(request_path,
                          None,
                          request_headers,
                          infile,
                          outfile,
                          base_env_dict=request_environ)

        outfile.flush()
        outfile.seek(0)

        status_code, status_message, header_list, body = RewriteResponse(outfile)
        logging.debug("Meta: result: %s %s %s", status_code, status_message, header_list)
        
        if status_code == 404:
            return False
        elif request_path == "/404.html":
            # fixes status for customized not found page
            logging.debug("Page's /404.html, so i'm changing status code")
            status_code = 404

        self.response.clear()
        for k in self.response.headers.keys():
            del self.response.headers[k]
        for h in header_list:
            parts = h.split(':')
            header_name = parts.pop(0)
            header_value = string.join(parts, ':')
            self.response.headers.add_header(header_name, header_value)
            
            # Save the Last-Modified header
            if header_name == 'Last-Modified':
            	HTTP_date = header_value

        # Use the If-Modified-Since header...
        if 'If-Modified-Since' in request_headers:
        	try:
        		format = '%a, %d %b %Y %H:%M:%S GMT'
        		request_date = datetime.strptime(request_headers['If-Modified-Since'].strip(), format)
        		response_date = datetime.strptime(HTTP_date.strip(), format)
        		if request_date >= response_date:
        			# Return 304 (Not Modified)
        			self.response.set_status(304, 'Not Modified')
        			return True
        	except ValueError:
        		pass 

        # If the request doesn't have an extension, return text/html
        basename, extension = os.path.splitext(request_path)
        if not extension:
          self.response.headers['Content-Type'] = "text/html"

        self.response.set_status(status_code, status_message)
        self.response.out.write(body)
        return True
        
    def system_dispatch(self):
        import logging
        import drydrop.app as app
        import datetime
        from drydrop.lib.utils import import_module
        from drydrop.app.core.appceptions import PageException

        # match internal route
        self.mapper.environ = self.request.environ
        controller = self.mapper.match(self.request.path)
        if controller == None:
            return False

        logging.debug("System: dispatching %s to %s", self.request.path, controller)

        # find the controller class
        action = controller['action']
        name = controller['controller']
        mod = import_module('drydrop.app.controllers.%s' % name)
        klass = "%sController" % name.capitalize()
        controller_class = mod.__dict__[klass]

        # add the route information as request parameters
        for param, value in controller.iteritems():
            self.request.GET[param] = value

        # instantiate controller
        controller_instance = controller_class(self.request, self.response, self)

        # get controller's methods
        before_method = controller_instance.__getattribute__('before_action')
        action_method = controller_instance.__getattribute__(action)
        after_method = controller_instance.__getattribute__('after_action')

        # see http://code.google.com/p/googleappengine/issues/detail?id=732
        self.response.headers['Cache-Control'] = "no-cache"
        expires = datetime.datetime.today() + datetime.timedelta(0, -1)
        self.response.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # call action methods
        try:
            before_result = before_method()
            if before_result:
                return
            
            action_result = action_method()
            if action_result:
                return
        
            after_result = after_method()
            if after_result:
                return
        except PageException:
            pass 
            
    def load_or_init_settings(self):
        from drydrop.app.models import Settings
        
        # fetch settings
        settings = Settings.all().filter("domain =", os.environ['SERVER_NAME']).fetch(1)
        if len(settings)==0:
            s = Settings()
            s.source = "http://github.com/darwin/drydrop/raw/master/tutorial"
            s.config = "site.yaml"
            s.domain = os.environ['SERVER_NAME']
            s.put()
            settings = [s]
        self.settings = settings[0]
    
    def init_vfs(self):
        from drydrop.app.core.vfs import LocalVFS, GAEVFS
        if self.settings.source.startswith('/'):
            vfs_class = LocalVFS
        else:
            vfs_class = GAEVFS
        self.vfs = vfs_class(self.settings)
    
    def read_config_source_or_provide_default_one(self):
        config_source = None
        if self.settings.config:
            try:
                config_source = self.vfs.get_resource(self.settings.config).content
            except:
                pass
        if config_source is not None:
            config_source = config_source.decode('utf-8')
        else:
            config_source = DEFAULT_CONFIG_SOURCE
        return config_source
    
    def post(self, *args, **kvargs):
        if self.request.POST.has_key('_method'):
            if self.request.POST['_method'] == 'put':
                self.request.environ['REQUEST_METHOD'] = 'PUT'
            elif self.request.POST['_method'] == 'delete':
                self.request.environ['REQUEST_METHOD'] = 'DELETE'

        self.route(*args, **kvargs)

    def get(self, *args, **kvargs):
        self.route(*args, **kvargs)

    def put(self, *args, **kvargs):
        self.route(*args, **kvargs)

    def delete(self, *args, **kvargs):
        self.route(*args, **kvargs)

    def route(self):
        from drydrop.app.core.appceptions import PageError

        try:
            # load self.settings
            self.load_or_init_settings()

            # init self.vfs
            self.init_vfs()

            # read site.yaml
            config_source = self.read_config_source_or_provide_default_one()

            # perform dispatch on meta server and finish if response was successfull
            dispatched = self.meta_dispatch(self.settings.source, config_source, self.request.path, self.request.headers, self.request.environ)

            # perform system dispatch (/admin section, welcome page, etc.)
            if not dispatched: 
                res = self.system_dispatch()
                if res == False:
                    # prepare 404 response
                    # TODO: fake headers and environ
                    dispatched404 = self.meta_dispatch(self.settings.source, config_source, "/404.html", self.request.headers, self.request.environ)
                    if not dispatched404:
                        # need to dispatch our stock 404 response
                        base_controller = self.get_base_controller()
                        try:
                            base_controller.notfound(404, 'File "%s" Not Found' % self.request.path)        
                        except PageError:
                            pass
        
        except Exception, e:
            # need to dispatch error response
            base_controller = self.get_base_controller()
            base_controller.error(404, 'Unable to process the page<br/>%s' % e)


class Application(object):

    def __call__(self, environ, start_response):
        import logging
        import sys

        request = webapp.Request(environ)
        response = webapp.Response()
        Application.active_instance = self

        handler = AppHandler()
        handler.initialize(request, response)

        groups = []
        try:
            method = environ['REQUEST_METHOD']
            if method == 'GET':
                handler.get(*groups)
            elif method == 'POST':
                handler.post(*groups)
            elif method == 'HEAD':
                handler.head(*groups)
            elif method == 'OPTIONS':
                handler.options(*groups)
            elif method == 'PUT':
                handler.put(*groups)
            elif method == 'DELETE':
                handler.delete(*groups)
            elif method == 'TRACE':
                handler.trace(*groups)
            else:
                handler.error(501)
        except:
            logging.exception(sys.exc_info()[1])
            import sys
            from drydrop.lib.nice_traceback import show_error
            show_error(handler, 500)

        handler.response.wsgi_write(start_response)
        return ['']

def main():
    import sys
    import logging
    from google.appengine.api import users

    if LOCAL:
        from google.appengine.tools.dev_appserver import FakeFile
        FakeFile.SetAllowedPaths('/', [])
        sys.meta_path = [] # disables python sandbox in local version
    
    # GENERATED: here we will setup import paths for baked version !!!
    # the domain: os.environ['SERVER_NAME']
    from google.appengine.api import urlfetch
    if not urlfetch.__dict__.has_key("old_fetch"):
        urlfetch.old_fetch = urlfetch.fetch
        def new_fetch(*arguments, **keywords):
            import logging
            from google.appengine.api import urlfetch
            logging.info("Fetching: %s", arguments[0])
            return urlfetch.old_fetch(*arguments, **keywords)
        urlfetch.fetch = new_fetch

    logging.getLogger().setLevel(logging.DEBUG)
    application = Application()
    try:
        from firepython.middleware import FirePythonWSGI
        if LOCAL or users.is_current_user_admin():
            application = FirePythonWSGI(application)
    except:
        pass
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
