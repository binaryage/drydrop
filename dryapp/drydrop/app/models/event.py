# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model
from drydrop.lib.properties import JSONProperty

class Event(db.Expando, Model):
    author = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    code = db.IntegerProperty(default=0)
    action = db.StringProperty()
    domain = db.StringProperty()
    info = db.TextProperty()
