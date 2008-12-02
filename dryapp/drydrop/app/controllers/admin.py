# -*- mode: python; coding: utf-8 -*-
import logging
from drydrop.app.core.controller import AuthenticatedController
from google.appengine.api import memcache, users

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
        
    def reindex(self):
        command = self.params.get('command')
        if command=='go':
            return self.render_json_response({
                'counter': 0,
                'message': 'start!'
            })
        else:
            counter = int(self.params.get('counter'))
            if counter==10:
                return self.render_json_response({
                    'finished': True,
                    'message': 'done!'
                })
            else:
                counter = counter + 1
                return self.render_json_response({
                    'counter': counter,
                    'message': 'counting %d' % counter
                })
                
    
    def _generate_file_index(self):
        file_index = self.handler.vfs.list_index()
        return file_index
    
    def browser(self):
        self.view['files'] = self._generate_file_index()
        self.render_view("admin/browser.html")

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

    def flush_memcache(self):
        memcache.flush_all()
        self.render_text("OK")

    def clear_datastore(self):
        clear_store()
        self.render_text("removed up to 100 objects from each kind")
        
    def update_option(self):
        id = self.params.get('id')
        if not id:
            return self.json_error('No option id specified')
            
        known_options = ['source', 'config']
        if not id in known_options:
            return self.json_error('Unknown option id (%s)' % id)

        value = self.params.get('value') or ""
        self.handler.settings.__setattr__(id, value)
        self.handler.settings.put()
            
        return self.render_text(value)