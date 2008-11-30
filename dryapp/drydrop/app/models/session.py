# -*- mode: python; coding: utf-8 -*-
import string
import logging
import google.appengine.ext.db as db
from drydrop.app.core.model import Model

class Session(db.Expando, Model):
    
    def __unicode__(self):
        props = self.dynamic_properties()
        a = []
        for k in props:
            a.append("%s=%s" % (k, getattr(self, k)))
        return "[%s]" % string.join(a, ', ')