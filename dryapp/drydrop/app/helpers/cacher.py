# -*- mode: python; coding: utf-8 -*-
from lib.utils import *
from google.appengine.api import memcache

def url_cache(fn, timeout=0):
    def wrapper(self, *arguments, **keywords):
        d = self.params.mixed() # shallow copy
        callback = d['callback']
        del d['callback']
        del d['_']
        hashkey = str(hash_dict(d))
        if not d.has_key('nocache'):
            cached_response = memcache.get(hashkey)
            if cached_response:
                self.handler.response = cached_response
                val = self.handler.response.out.getvalue()
                self.handler.response.clear()
                self.handler.response.out.write(val.replace("__callback__", callback))
                return
        res = fn(self, *arguments, **keywords)
        memcache.set(hashkey, self.handler.response, timeout)
        val = self.handler.response.out.getvalue()
        self.handler.response.clear()
        self.handler.response.out.write(val.replace("__callback__", callback))
        return res
    
    return wrapper