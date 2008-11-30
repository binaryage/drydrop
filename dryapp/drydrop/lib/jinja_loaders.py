# -*- mode: python; coding: utf-8 -*-
import os.path
from drydrop_handler import LOCAL
from jinja2 import FileSystemLoader, TemplateNotFound
from drydrop.lib.utils import universal_read

class InternalTemplateLoader(FileSystemLoader):
    
    def __init__(self, searchpath, encoding='utf-8'):
        if isinstance(searchpath, basestring):
            searchpath = [searchpath]
        self.searchpath = list(searchpath)
        if LOCAL:
            self.searchpath = [p.replace('.zip', '') for p in self.searchpath]
        self.encoding = encoding
    
    def get_source(self, environment, template):
        if LOCAL:
            # during local development, templates are files and we want "uptodate" feature
            return FileSystemLoader.get_source(self, environment, template)
        
        # on production server template may come from zip file
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, template)
            contents = universal_read(filename)
            if contents is None:
                continue
            contents = contents.decode(self.encoding)
            def uptodate():
                return True
            return contents, filename, uptodate
        raise TemplateNotFound(template)