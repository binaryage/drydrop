# -*- mode: python; coding: utf-8 -*-
import logging
import os
from drydrop.app.core.controller import AuthenticatedController
from google.appengine.api import memcache, users
from drydrop.app.core.events import log_event
from drydrop.app.models import Event, Settings

class AdminController(AuthenticatedController):

    def before_action(self, *arguments, **keywords):
        if super(AdminController, self).before_action(*arguments, **keywords): return True
        self.view.update({
            'body_class': '',
            'user': self.user,
            'users': users,
            'settings': self.handler.settings
        })
        if not users.is_current_user_admin():
            self.render_view('admin/not_admin.html', {'body_class': 'has_error'})
            return True
        
    def index(self):
        self.render_view("admin/index.html")
        
    def events_flusher(self):
        domain = os.environ['SERVER_NAME']
        deleted = Event.clear(False, 1000, domain=domain)
        done = deleted<1000
        log_event("Removed all events")
        message = 'removed %d event(s)' % deleted
        if not done: message += ' ...'
        return self.render_json_response({
            'finished': done,
            'message': message
        })
        
    def flusher(self):
        log_event("Flushed resource cache")
        vfs = self.handler.vfs
        done, num = vfs.flush_resources()
        message = 'flushed %d resource(s)' % num
        if not done: message += ' ...'
        return self.render_json_response({
            'finished': done,
            'message': message
        })
    
    def _generate_resource_index(self):
        vfs = self.handler.vfs
        resources = vfs.get_all_resources()
        if resources is None:
            resources = []
        return resources
    
    def cache(self):
        self.view['resources'] = self._generate_resource_index()
        self.render_view("admin/cache.html")

    def settings(self):
        self.render_view("admin/settings.html")

    def config(self):
        import pygments
        import pygments.lexers
        import pygments.formatters
        lexer = pygments.lexers.get_lexer_by_name('yaml')
        formatter = pygments.formatters.HtmlFormatter()
        config_source_formatted = pygments.highlight(self.handler.read_config_source_or_provide_default_one(), lexer, formatter)
        self.render_view("admin/config.html", { 'config_source_formatted': config_source_formatted })
    
    def events(self):
        offset = int(self.params.get("offset", 0))
        limit = int(self.params.get("limit", 50))
        events = Event.all().filter("domain =", os.environ['SERVER_NAME']).order('-date').fetch(limit, offset)
        res = []
        for e in events:
            res.append({
                "author": unicode(e.author),
                "action": unicode(e.action),
                "info": unicode(e.info),
                "code": e.code,
                "date": e.date
            })
        
        return self.render_json_response({
            'status': 0,
            'data': res
        })

    def flush_memcache(self):
        memcache.flush_all()
        self.render_text("OK")

    def update_option(self):
        id = self.params.get('id')
        domain=os.environ['SERVER_NAME']
        if not id:
            return self.json_error('No option id specified')
            
        known_options = ['source', 'config', 'github_login', 'github_token']
        if not id in known_options:
            return self.json_error('Unknown option id (%s)' % id)

        value = self.params.get('value') or ""
        log_event("Changed <code>%s</code> to <code>%s</code>" % (id, value))
        settings = self.handler.settings
        settings.__setattr__(id, value)
        settings.version = settings.version + 1 # this effectively invalidates cache
        settings.domain = domain
        settings.put()
            
        return self.render_text(value)

    def _generate_domain_index(self):
        settings = Settings.all()
        domains = []
        for setting in settings:
          domains.append(setting.domain)

        return domains

    def domains(self):
        self.view['domains'] = self._generate_domain_index()
        self.render_view("admin/domains.html")
