# -*- mode: python; coding: utf-8 -*-
import os
import re
import logging
import datetime
import mimetypes
import time
import jinja2
import email.Utils
from Cookie import BaseCookie
from routes import url_for
from google.appengine.ext.webapp import Response
from google.appengine.api import memcache, users
from drydrop.lib.json import json_encode
from drydrop_handler import DRY_ROOT, APP_ROOT, APP_ID, VER_ID, LOCAL
from drydrop.app.models import *
from drydrop.app.core.appceptions import *
from drydrop.lib.utils import *
from drydrop.lib.jinja_loaders import InternalTemplateLoader
from drydrop.app.helpers.buster import cache_buster

class AbstractController(object):
    def __init__(self, request, response, handler):
        self.request = request
        self.response = response
        self.handler = handler
        self.view = {'params': request.params }
        self.params = request.params
        self.emited = False
        self.cookies = request.cookies
    
    def render(self, template_name):
        env = jinja2.Environment(loader = InternalTemplateLoader(os.path.join(DRY_ROOT, 'app', 'views')))
        try:
            template = env.get_template(template_name)
        except jinja2.TemplateNotFound:
            raise jinja2.TemplateNotFound(template_name)
        content = template.render(self.view)
        if LOCAL:
            content = cache_buster(content)
        self.response.out.write(content)
            
    def before_action(self):
        pass
    
    def after_action(self):
        pass
    
    def render_view(self, file_name, params = None):
        if params:
            self.view.update(params)
        self.response.headers['Content-Type'] = 'text/html'
        self.render(file_name)
        self.emited = True
    
    def render_text(self, text):
        self.response.headers['Content-Type'] = 'text/html'
        if LOCAL:
            text = cache_buster(text)
        self.response.out.write(text)
        self.emited = True
    
    def render_html(self, html, params = None):
        if params:
            self.view.update(params)
        if LOCAL:
            html = cache_buster(html)
        self.response.out.write(html)
        self.emited = True
    
    def render_xml(self, xml):
        self.response.headers['Content-Type'] = 'text/xml'
        self.render(file_name)
        self.emited = True
    
    def render_json(self, json):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json)
        self.emited = True
    
    def redirect_to(self, url):
        """Redirects to a specified url"""
        # self.handler.redirect(url)
        # self.emited = True
        # raise PageRedirect, (url)
        
        # mrizka delala problemy pri claimovani openid
        m = re.match(r'^(.*)#.*?$', url)
        if m: url = m.group(1)
        
        logging.info("Redirecting to: %s" % url)
        
        # send the redirect!  we use a meta because appengine bombs out sometimes with long redirect urls
        self.response.out.write("<html><head><meta http-equiv=\"refresh\" content=\"0;url=%s\"></head><body></body></html>" % (url,))
        self.emited = True
        raise PageRedirect, (url)

    def notfound(self, code, message = None):
        self.response.set_status(code, str(message))
        if message is None: message = Response.http_status_message(code)
        self.view['message'] = message
        self.view['code'] = code
        self.render_view('system/notfound.html')
    
    def error(self, code, message = None):
        self.response.set_status(code, str(message))
        if message is None: message = Response.http_status_message(code)
        self.view['message'] = message
        self.view['code'] = code
        self.render_view('system/error.html')

class CookieController(AbstractController):
    def set_cookie(self, key, value='', max_age=None,
                   path='/', domain=None, secure=None, httponly=False,
                   version=None, comment=None):
        """
        Set (add) a cookie for the response
        """
        cookies = BaseCookie()
        cookies[key] = value
        for var_name, var_value in [
            ('max-age', max_age),
            ('path', path),
            ('domain', domain),
            ('secure', secure),
            ('HttpOnly', httponly),
            ('version', version),
            ('comment', comment),
            ]:
            if var_value is not None and var_value is not False:
                cookies[key][var_name] = str(var_value)
            if max_age is not None:
                cookies[key]['expires'] = max_age
        header_value = cookies[key].output(header='').lstrip()
        self.response.headers._headers.append(('Set-Cookie', header_value))
    
    def delete_cookie(self, key, path='/', domain=None):
        """
        Delete a cookie from the client.  Note that path and domain must match
        how the cookie was originally set.
        This sets the cookie to the empty string, and max_age=0 so
        that it should expire immediately.
        """
        self.set_cookie(key, '', path=path, domain=domain, max_age=0)
    
    def unset_cookie(self, key):
        """
        Unset a cookie with the given name (remove it from the
        response).  If there are multiple cookies (e.g., two cookies
        with the same name and different paths or domains), all such
        cookies will be deleted.
        """
        existing = self.response.headers.get_all('Set-Cookie')
        if not existing:
            raise KeyError("No cookies at all have been set")
        del self.response.headers['Set-Cookie']
        found = False
        for header in existing:
            cookies = BaseCookie()
            cookies.load(header)
            if key in cookies:
                found = True
                del cookies[key]
            header = cookies.output(header='').lstrip()
            if header:
                self.response.headers.add('Set-Cookie', header)
        if not found:
            raise KeyError("No cookie has been set with the name %r" % key)

class BaseController(CookieController):
    SESSION_MEMCACHE_TIMEOUT = 0
    CACHE_TIMEOUT = 7200
    
    def serve_static_file(self, base_path, path, more = None, more_placeholder = None, filter=None):
        file_path = os.path.join(base_path, path)
        try:
            logging.debug('Serving static file %s', file_path)
            data = universal_read(file_path)
            if filter: data = filter(data, base_path, path)
            mime_type, encoding = mimetypes.guess_type(path)
            self.response.headers['Content-Type'] = mime_type
            self.set_caching_headers(self.CACHE_TIMEOUT)
            if more and more_placeholder:
                data = data.replace(more_placeholder, more)
            self.response.out.write(data)
            if more and not more_placeholder:
                self.response.out.write(more)
        except IOError:
            return self.error(404, '404 File %s Not Found' % path)
    
    def set_caching_headers(self, max_age, public = True):
        self.response.headers['Expires'] = email.Utils.formatdate(time.time() + max_age, usegmt=True)
        cache_control = []
        if public: cache_control.append('public')
        cache_control.append('max-age=%d' % max_age)
        self.response.headers['Cache-Control'] = ', '.join(cache_control)

    def render_json_response(self, data):
        json = json_encode(data, nice=LOCAL)

        is_test = self.params.get('test')
        if is_test:
            # this branch is here for testing purposes
            return self.render_html("<html><body><pre>%s</pre></body></html>" % json)

        callback = self.params.get('callback')
        if callback:
            # JSONP style
            self.render_text("__callback__(%s);" % json)
        else:
            # classic style
            self.render_json(json)

    def format_json_response(self, message, code=1):
        return {
            "status": code,
            "message": message,
        }
        
    def json_error(self, message, code=1):
        self.render_json_response(self.format_json_response(message, code))
        
    def json_ok(self, message = "OK"):
        self.render_json_response(self.format_json_response(message, 0))

class SessionController(BaseController):
    SESSION_KEY = 'session'
    SESSION_COOKIE_TIMEOUT_IN_SECONDS = 60*60*24*14
    session = None
    
    def _session_memcache_id(self, session_id):
        return "session-"+session_id
    
    def create_session(self, user_id):
        self.session = Session(user_id=user_id)
        self.session.save()
        logging.debug("Created session: %s", self.session.get_id())
    
    def load_session(self):
        if self.session: return self.session
        
        logging.debug("Loading session ...")
        # look for session id in request and cookies
        session_id = self.request.get(self.SESSION_KEY)
        if not session_id: session_id = self.cookies.get(self.SESSION_KEY)
        if not session_id:
            logging.debug("session_id not found in %s", self.cookies)
            return None
        
        # hit memcache first
        cache_id = self._session_memcache_id(session_id)
        self.session = memcache.get(cache_id)
        if self.session:
            logging.debug("Session found in memcache %s", self.session)
            return self.session
        
        # hit database if not in memcache
        self.session = Session.get(session_id)
        if self.session:
            logging.debug("Session loaded from store %s", self.session)
            memcache.set(cache_id, self.session, self.SESSION_MEMCACHE_TIMEOUT)
            return self.session
        
        # session not found
        return None
    
    def store_session(self):
        assert self.session
        cache_id = self._session_memcache_id(self.session.get_id())
        logging.debug("Storing session (%s) into memcache as %s" % (self.session, cache_id))
        self.set_cookie(self.SESSION_KEY,
            str(self.session.key()),
            max_age=self.SESSION_COOKIE_TIMEOUT_IN_SECONDS
        )
        memcache.set(cache_id, self.session, self.SESSION_MEMCACHE_TIMEOUT)
        self.session.save()
    
    def clear_session_cookie(self):
        logging.debug("Clearing session cookie (%s)" % self.SESSION_KEY)
        self.delete_cookie(self.SESSION_KEY)
    
    def clear_session(self):
        if not self.session:
            if not self.load_session(): return
        logging.debug("Clearing session %s", self.session)
        cache_id = self._session_memcache_id(self.session.get_id())
        memcache.delete(cache_id)
        self.session.delete()

class AuthenticatedController(SessionController):
    
    def __init__(self, *arguments, **keywords):
        super(AuthenticatedController, self).__init__(*arguments, **keywords)
        self.user = None
        
    def authenticate_user(self, url=None):
        self.user = users.get_current_user()
        if not self.user:
            return self.redirect_to(users.create_login_url(url or self.request.url))
        logging.info('Authenticated as user %s', self.user)
    
    def before_action(self, *arguments, **keywords):
        if super(AuthenticatedController, self).before_action(*arguments, **keywords): return True
        return self.authenticate_user()