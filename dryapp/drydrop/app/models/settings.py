# -*- mode: python; coding: utf-8 -*-
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model
from drydrop.lib.properties import JSONProperty, NiceDateTimeProperty

class Settings(db.Expando, Model):
    index = JSONProperty()
    source = db.StringProperty()
    config = db.StringProperty()
    last_updated = NiceDateTimeProperty()
    last_reindexed = NiceDateTimeProperty()
