# -*- mode: python; coding: utf-8 -*-
import os
import os.path
import errno
from string import *
from random import choice
from string import digits, letters
import logging
import urlparse
import re
import simplejson
import sys
import zipfile
import urllib
from drydrop_handler import LOCAL

def import_module(name):
    __import__(name)
    return sys.modules[name]
      
zipfile_cache = {}
def universal_read(path):
    if LOCAL: 
        path = path.replace('.zip', '')
        return open(path, 'r').read()
    m = re.match(r'^(.*?)/([^/]+?)\.zip/(.*)$', path)
    if m is None: return open(path, 'r').read()

    global zipfile_cache
    
    zipfilename = os.path.join(m.group(1), m.group(2)+".zip")
    zipfile_object = zipfile_cache.get(zipfilename)
    if zipfile_object is None:
        try:
            zipfile_object = zipfile.ZipFile(zipfilename)
        except (IOError, RuntimeError), err:
            logging.error('Can\'t open zipfile %s: %s', zipfilename, err)
            return None
        zipfile_cache[zipfilename] = zipfile_object
    relfilename = os.path.join(m.group(2), m.group(3))
    return zipfile_object.read(relfilename)

def read_utf8(path):
    return universal_read(path).decode('utf-8')
    
def camelize(string):
    string = string.replace('-', '_')
    return ''.join([word.capitalize() for word in string.split('_')])

def camelizejs(string):
    string = string.replace('-', '_')
    parts = string.split('_')
    first = parts.pop(0)
    return first+''.join([word.capitalize() for word in parts])
    
def decamelizejs(string):
    s = re.sub(r'([A-Z])', '_\\1', string)
    return s.lower()

def uniqueid(length):
    POOL = digits + letters
    return ''.join([choice(POOL) for i in range(length)])
    
def decode_json_param(value):
    try:
        return simplejson.loads(value)
    except:
        return str(value) # return it as string

class struct: 
    pass
    
def dict2struct(dct):
    if isinstance(dct,dict):
        s=struct()
        for key,val in dct.iteritems():
            setattr(s,key,dict2struct(val))
        return s
    elif isinstance(dct,list):
        return [dict2struct(val) for val in dct]
    else:
        return dct

def array2dict(array,key):
    out={}
    for item in array:
        out[item[key]]=item
    return out

def dict2array(dct):
    arr=[]
    for item in dct.values():
        arr+=item
    return arr
    
def struct2dict(array,key):
    out={}
    for item in array:
        out[getattr(item,key)]=item
    return out

def lastitem(array):
    return array[len(array)-1]
        
def miditem(array):
    return array[len(array)/2]

def filter_dict(mydict,*args,**kwargs):
    out={}
    only=kwargs.get('only')
    remove=kwargs.get('remove')
    if only:
        out.update(dict([ (str(key),mydict[key]) for key in mydict if key in only]))
    if remove:    
        out.update(dict([ (str(key),mydict[key]) for key in mydict if key not in only]))
    return out

def hash_dict(mydict):
    return hash(tuple(mydict.iteritems()))

def key_dict(d):
    return urllib.urlencode(d)
    
def lookup_method(selector, context):
    selectors = selector.split('.')
    method_name = selectors.pop()
    class_name = selectors.pop()
    module_name = join(selectors, '.')
    module = import_module(module_name)
    klass = module.__dict__[class_name]   
    instance = klass(context)
    return instance.__getattribute__(method_name)
    
_base_js_escapes = (
    ("\\", "\\\\"),
    ("'", "\\'"),
    ("\n", "\\\n"),
    
)

def open_if_exists(filename, mode='r'):
    """Returns a file descriptor for the filename if that file exists, otherwise `None`."""
    try:
        return open(filename, mode)
    except IOError, e:
        pass

def escape_codes(start, stop):
    return tuple([('%c' % z, '\\x%02X' % z) for z in range(start, stop)])

# Escape every ASCII character with a value less than 32.
_js_escapes = (_base_js_escapes+escape_codes(0,9)+escape_codes(11,32))

def escapejs(value):
    """Hex encodes characters for use in JavaScript strings."""
    for bad, good in _js_escapes:
        value = value.replace(bad, good)
    return value        
    
def pluralize(noun):
    if re.search('[sxz]$', noun):
        return re.sub('$', 'es', noun)
    elif re.search('[^aeioudgkprt]h$', noun):
        return re.sub('$', 'es', noun)
    elif re.search('[^aeiou]y$', noun):
        return re.sub('y$', 'ies', noun)
    else:
        return noun + 's'