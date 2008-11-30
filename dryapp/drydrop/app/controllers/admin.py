# -*- mode: python; coding: utf-8 -*-
from drydrop.app.core.controller import AuthenticatedController
from google.appengine.api import memcache

class AdminController(AuthenticatedController):

    def index(self):
        self.render_text("TODO: create admin section")
    
    def flush_memcache(self):
        memcache.flush_all()
        self.render_text("OK")

    def clear_datastore(self):
        clear_store()
        self.render_text("removed up to 100 objects from each kind")    