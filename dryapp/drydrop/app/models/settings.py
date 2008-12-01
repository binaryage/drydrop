# -*- mode: python; coding: utf-8 -*-
import string
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class Settings(db.Expando, Model):
    pass