# -*- mode: python; coding: utf-8 -*-
import logging
import os
import os.path
from drydrop.lib.utils import open_if_exists

class VFS(object):
    """Virtual File System == filesystem abstraction for DryDrop"""
    def __init__(self):
        super(VFS, self).__init__()
    
    def get_content(self, path):
        logging.warning('get_content not implemented in %s', self.__class__.__name__)
        return None
    
    def put_content(self, path, content=None):
        logging.warning('put_content not implemented in %s', self.__class__.__name__)

    def get_index(self, path):
        logging.warning('get_index not implemented in %s', self.__class__.__name__)
    
    def list_index(self, filter=None):
        logging.warning('list_index not implemented in %s', self.__class__.__name__)
        return []
        
    def clear_index(self):
        logging.warning('clear_index not implemented in %s', self.__class__.__name__)
        
    def add_index(self, items):
        logging.warning('add_index not implemented in %s', self.__class__.__name__)
        
    def remove_index(self, paths):
        logging.warning('remove_index not implemented in %s', self.__class__.__name__)
        
class BaseVFS(VFS):
    
    def clear_index(self):
        index = self.settings.index
        for k, v in index.iteritems():
            self.put_content(k, None)
        index = {}

    def add_index(self, items):
        index = self.settings.index
        for k, v in items.iteritems():
            v['state'] = 'dirty'
            index[k] = v
    
    def remove_index(self, paths):
        if not isinstance(paths, list):
            paths = [paths]
        
        index = self.settings.index
        for p in paths:
            if not index.has_key(p):
                continue
            del index[p]
            self.put_content(p, None)
            
    def list_index(self, filter=None):
        index = self.settings.index
        if filter is None:
            return index
        
        res = {}
        for k, v in index.iteritems():
            if filter.match(k):
                res[k] = v
        
        return res
        
class DevVFS(BaseVFS):
    """DevVFS - VFS for local development"""
    def __init__(self, settings):
        super(DevVFS, self).__init__()
        self.settings = settings
    
    def get_content(self, path):
        root = self.settings.source
        if not root:
            return None
        
        filepath = os.path.join(root, path)
        f = open_if_exists(filepath)
        if f is None:
            return None
        try:
            contents = f.read()
        finally:
            f.close()
        return contents

    def put_content(self, path, content):
        logging.warning('put_content is no-op in  %s', self.__class__.__name__)

    # def list_index(self, filter=None):
    #     data = []
    #     for dirpath, dirnames, filenames in os.walk(self.root):
    #         # has to be pruning dirnames so ugly?
    #         visible_dirnames = [x for x in dirnames if not x.startswith('.')]
    #         del dirnames[:]
    #         dirnames.extend(visible_dirnames)
    #         for filename in filenames:
    #             if not filename.startswith('.'):
    #                 fullname = os.path.join(dirpath, filename)
    #                 if filter is None or filter.match(fullname):
    #                     data.append((fullname, {}))
    #     
    #     return data

class GAEVFS(BaseVFS):
    
    def __init__(self, settings):
        super(GAEVFS, self).__init__()
        self.settings = settings