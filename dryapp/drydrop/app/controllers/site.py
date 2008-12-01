# -*- mode: python; coding: utf-8 -*-
import logging
from drydrop.app.core.controller import BaseController

class SiteController(BaseController):

    def serve(self):
        path = self.params.path
        logging.debug('Serving site file %s', path)
        data = self.handler.vfs.get(path)
        if data is None:
            raise UnableToServe()
            
        mime_type, encoding = mimetypes.guess_type(path)
        self.response.headers['Content-Type'] = mime_type
        self.set_caching_headers(self.CACHE_TIMEOUT)
        self.response.out.write(data)
