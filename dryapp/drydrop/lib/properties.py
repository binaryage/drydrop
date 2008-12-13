# -*- mode: python; coding: utf-8 -*-
import logging
import pickle
import base64
from google.appengine.ext import db
from google.appengine.api import datastore_types
from drydrop.lib.utils import *
from drydrop.lib.json import *
        
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
