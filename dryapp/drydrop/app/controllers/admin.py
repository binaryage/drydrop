# -*- mode: python; coding: utf-8 -*-
from drydrop.app.core.controller import AuthenticatedController
from google.appengine.api import memcache, users

class AdminController(AuthenticatedController):

    def before_action(self, *arguments, **keywords):
        if super(AdminController, self).before_action(*arguments, **keywords): return True
        self.view.update({
            'body_class': '',
            'user': self.user,
            'users': users
        })
        if not users.is_current_user_admin():
            self.render_view('admin/not_admin.html', {'body_class': 'has_error'})
            return True
        
    def index(self):
        self.render_view("admin/index.html")
    
    def _generate_file_list(self):
        file_list = self.handler.vfs.list()
        return file_list
    
    def browser(self):
        self.view['files'] = self._generate_file_list()
        self.render_view("admin/browser.html")

    def settings(self):
        self.render_view("admin/settings.html")

    def flush_memcache(self):
        memcache.flush_all()
        self.render_text("OK")

    def clear_datastore(self):
        clear_store()
        self.render_text("removed up to 100 objects from each kind")    