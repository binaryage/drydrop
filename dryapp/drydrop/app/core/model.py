# -*- mode: python; coding: utf-8 -*-
import re
import simplejson
from drydrop.lib.utils import *
from drydrop.lib.properties import *
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from drydrop.lib.json import json_encode

class Model(object): 
    
    def __str__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        a = []
        for k, v in self.__dict__.iteritems():
            a.append("%s=%s" % (k, v))
        return "[%s]" % string.join(a, ', ')
            

    def get_id(self):
        return str(self.key())
        
    @classmethod
    def create(cls, *arguments, **keywords):
        instance = cls(*arguments, **keywords)
        instance.put()
        return instance

    @classmethod
    def find(cls, **params):
        query = cls.all()
        for name in params:
            query = query.filter("%s =" % name, params[name])
        return query.get()

    @classmethod
    def clear(cls, verbose=False, count=100000000):
        if verbose: logging.info("clearing %s", cls.model)
        deleted = 0
        while count>0:
            records = cls.all().fetch(100)
            if len(records)==0: break
            deleted += len(records)
            db.delete(records)
            count -= 100
        return deleted
