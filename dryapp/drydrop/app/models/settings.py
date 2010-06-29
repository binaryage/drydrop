# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class Settings(db.Expando, Model):
    source = db.StringProperty()
    config = db.StringProperty()
    version = db.IntegerProperty(default=1)
    domain = db.StringProperty()
    last_updated = db.DateTimeProperty()
    github_login = db.StringProperty() # for private repos
    github_token = db.StringProperty() # for private repos
