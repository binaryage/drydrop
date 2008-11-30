# -*- mode: python; coding: utf-8 -*-
import logging
from google.appengine.ext import db
from google.appengine.api import datastore_types
from django.utils import simplejson
from drydrop.lib.utils import *
from drydrop.lib.json import *
import pickle
import base64

CUSTOM_DATETIME_INPUT_FORMATS = (
    '%d/%m/%y',              
    '%d-%m-%y',              
    '%d.%m.%y',              
    '%d/%m/%Y',              
    '%d-%m-%Y',              
    '%d.%m.%Y',
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'              
)

class NiceDateTimeProperty(db.DateTimeProperty):

    def get_value_for_form(self,instance):
        value = getattr(instance, self.name)
        if not value:
            return None
        else:
            return value.strftime("%d-%m-%Y")
    
    def get_timestamp(self):
        value = getattr(instance, self.name)
        if not value:
            return None
        return value.strftime("%H%M%S")
        
class JSONProperty(db.TextProperty):

    def get_value_for_datastore(self, model_instance):
        value = self.__get__(model_instance, model_instance.__class__)
        return db.Text(self._deflate(value))

    def validate(self, value):
        return value

    def make_value_from_datastore(self, value):
        return self._inflate(value)

    def _inflate(self, value):
        return json_parse(value)

    def _deflate(self, value):
        return json_encode(value)

class PickleProperty(db.BlobProperty):

    def get_value_for_datastore(self, model_instance):
        value = self.__get__(model_instance, model_instance.__class__)
        return db.Blob(self._deflate(value))

    def validate(self, value):
        return value

    def make_value_from_datastore(self, value):
        return self._inflate(value)

    def _inflate(self, value):
        try:
            return pickle.loads(value)
        except:
            return ""

    def _deflate(self, value):
        return pickle.dumps(value)
