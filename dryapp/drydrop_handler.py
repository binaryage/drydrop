# -*- mode: python; coding: utf-8 -*-

# try to not put here any imports, there is a bug in import caching in GAE:
# http://code.google.com/appengine/articles/django10_zipimport.html

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import os
import os.path

APP_ROOT = os.path.normpath(os.path.dirname(__file__))
DRY_ROOT = os.path.join(APP_ROOT, 'drydrop.zip')

LOCAL = os.environ["SERVER_SOFTWARE"].startswith("Development")
APP_ID = os.environ["APPLICATION_ID"]
VER_ID = os.environ["CURRENT_VERSION_ID"]

# tohle musi byt tvrda cesta, slouzi pro generovani nice tracebacku na ostrem serveru
DEVELOPMENT_PROJECT_ROOT = "/Users/woid/code/drydrop/dryapp/"

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
  m.connect('/admin', controller="admin", action="index")
  m.connect('/', controller="welcome", action="index")
  
  # Install the default routes as the lowest priority.  
  # m.connect(':controller/:action/:id', controller='welcome', action='index')
  
  # returns the mapper object. Do not remove.
  return m
  
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
    
    def route(self):
        import logging
        import datetime
        from drydrop.lib.utils import import_module
        from drydrop.app.core.appceptions import PageException

        # match the route
        self.mapper.environ = self.request.environ
        controller = self.mapper.match(self.request.path)
        if controller == None:
            raise Exception('No route for '+self.request.path)
            return

        logging.debug("Dispatching %s to %s", self.request.path, controller)

        # find the controller class
        import drydrop.app as app
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
        except Exception, e:
            # beep
            logging.exception(sys.exc_info()[1])
            import sys
            sys.__stdout__.write('\a')
            sys.__stdout__.flush()
            from drydrop.lib.nice_traceback import show_error
            show_error(handler, 500)

        handler.response.wsgi_write(start_response)
        return ['']

def main():
    import sys
    import logging
    logging.error("enter")

    if LOCAL:
        sys.meta_path = [] # disables python sandbox in local version
    
    # GENERATED: here we will setup import paths for baked version !!!

    from google.appengine.api import urlfetch
    if not urlfetch.__dict__.has_key("old_fetch"):
        urlfetch.old_fetch = urlfetch.fetch
        def new_fetch(*arguments, **keywords):
            import logging
            from google.appengine.api import urlfetch
            logging.info("Fetching: %s" % str(arguments))
            return urlfetch.old_fetch(*arguments, **keywords)
        urlfetch.fetch = new_fetch

    logging.getLogger().setLevel(logging.DEBUG)
    from firepython.middleware import FirePythonWSGI
    run_wsgi_app(FirePythonWSGI(Application()))

if __name__ == "__main__":
    main()