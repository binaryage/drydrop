"""Routes WSGI Middleware"""
import re
import logging

try:
    from paste.wsgiwrappers import WSGIRequest
except:
    pass

from routes.base import request_config

log = logging.getLogger('routes.middleware')

class RoutesMiddleware(object):
    """Routing middleware that handles resolving the PATH_INFO in
    addition to optionally recognizing method overriding."""
    def __init__(self, wsgi_app, mapper, use_method_override=True, 
                 path_info=True):
        """Create a Route middleware object
        
        Using the use_method_override keyword will require Paste to be
        installed, and your application should use Paste's WSGIRequest
        object as it will properly handle POST issues with wsgi.input
        should Routes check it.
        
        If path_info is True, then should a route var contain
        path_info, the SCRIPT_NAME and PATH_INFO will be altered
        accordingly. This should be used with routes like:
        
        .. code-block:: python
        
            map.connect('blog/*path_info', controller='blog', path_info='')
        
        """
        self.app = wsgi_app
        self.mapper = mapper
        self.use_method_override = use_method_override
        self.path_info = path_info
        log.debug("Initialized with method overriding = %s, and path info "
                  "altering = %s", use_method_override, path_info)
    
    def __call__(self, environ, start_response):
        """Resolves the URL in PATH_INFO, and uses wsgi.routing_args
        to pass on URL resolver results."""
        config = request_config()
        config.mapper = self.mapper
        
        old_method = None
        if self.use_method_override:
            req = WSGIRequest(environ)
            req.errors = 'ignore'
            if '_method' in environ.get('QUERY_STRING', '') and \
                '_method' in req.GET:
                old_method = environ['REQUEST_METHOD']
                environ['REQUEST_METHOD'] = req.GET['_method'].upper()
                log.debug("_method found in QUERY_STRING, altering request"
                          " method to %s", environ['REQUEST_METHOD'])
            elif is_form_post(environ) and '_method' in req.POST:
                old_method = environ['REQUEST_METHOD']
                environ['REQUEST_METHOD'] = req.POST['_method'].upper()
                log.debug("_method found in POST data, altering request "
                          "method to %s", environ['REQUEST_METHOD'])
        
        # Run the actual route matching
        # -- Assignment of environ to config triggers route matching
        config.environ = environ
        
        match = config.mapper_dict
        route = config.route
        
        if old_method:
            environ['REQUEST_METHOD'] = old_method
        
        urlinfo = "%s %s" % (environ['REQUEST_METHOD'], environ['PATH_INFO'])
        if not match:
            match = {}
            log.debug("No route matched for %s", urlinfo)
        else:
            log.debug("Matched %s", urlinfo)
            log.debug("Route path: '%s', defaults: %s", route.routepath, 
                      route.defaults)
            log.debug("Match dict: %s", match)
                
        environ['wsgiorg.routing_args'] = ((), match)
        environ['routes.route'] = route

        # If the route included a path_info attribute and it should be used to
        # alter the environ, we'll pull it out
        if self.path_info and match.get('path_info'):
            oldpath = environ['PATH_INFO']
            newpath = match.get('path_info') or ''
            environ['PATH_INFO'] = newpath
            if not environ['PATH_INFO'].startswith('/'):
                environ['PATH_INFO'] = '/' + environ['PATH_INFO']
            environ['SCRIPT_NAME'] += re.sub(r'^(.*?)/' + newpath + '$', 
                                             r'\1', oldpath)
            if environ['SCRIPT_NAME'].endswith('/'):
                environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'][:-1]
        
        response = self.app(environ, start_response)
        del config.environ
        del self.mapper.environ
        return response

def is_form_post(environ):
    """Determine whether the request is a POSTed html form"""
    if environ['REQUEST_METHOD'] != 'POST':
        return False
    content_type = environ.get('CONTENT_TYPE', '').lower()
    if ';' in content_type:
        content_type = content_type.split(';', 1)[0]
    return content_type in ('application/x-www-form-urlencoded',
                            'multipart/form-data')
