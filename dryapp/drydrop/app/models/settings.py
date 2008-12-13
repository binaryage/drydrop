# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class Settings(db.Expando, Model):
    source = db.StringProperty()
    config = db.StringProperty()
    version = db.IntegerProperty(default=1)
    last_updated = db.DateTimeProperty()