# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class File(db.Expando, Model):
    name = db.StringProperty()
    content = db.BlobProperty()
