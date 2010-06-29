# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class Resource(db.Expando, Model):
    path = db.StringProperty()
    generation = db.IntegerProperty()
    content = db.BlobProperty()
    domain = db.StringProperty()
    created_on = db.DateTimeProperty(auto_now_add=True)
