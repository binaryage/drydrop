# -*- mode: python; coding: utf-8 -*-
import logging
import os
import os.path
from drydrop.lib.utils import open_if_exists

class VFS(object):
    """Virtual File System == filesystem abstraction for DryDrop"""
    def __init__(self):
        super(VFS, self).__init__()
    
    def get(self, path):
        logging.warning('get not implemented in %s', self.__class__.__name__)
        return None
    
    def put(self, path, content, meta):
        logging.warning('put not implemented in %s', self.__class__.__name__)
    
    def list(self, filter=None):
        logging.warning('list not implemented in %s', self.__class__.__name__)
        return []
        
class DevVFS(VFS):
    """DevVFS - VFS for local development"""
    def __init__(self, root):
        super(DevVFS, self).__init__()
        self.root = root
    
    def get(self, path):
        filepath = os.path.join(self.root, path)
        f = open_if_exists(filepath)
        if f is None:
            return None
        try:
            contents = f.read()
        finally:
            f.close()
        return contents

    def put(self, path, content, meta):
        logging.warning('put is no-op in  %s', self.__class__.__name__)

    def list(self, filter=None):
        data = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            # has to be pruning dirnames so ugly?
            visible_dirnames = [x for x in dirnames if not x.startswith('.')]
            del dirnames[:]
            dirnames.extend(visible_dirnames)
            for filename in filenames:
                if not filename.startswith('.'):
                    fullname = os.path.join(dirpath, filename)
                    if filter is None or filter.match(fullname):
                        data.append((fullname, {}))
        
        return data

class GAEVFS(VFS):
    def __init__(self, root):
        super(GAEVFS, self).__init__()
        self.root = root