# -*- mode: python; coding: utf-8 -*-
import os
import re
import os.path
import logging
import datetime
from drydrop.lib.utils import open_if_exists
from drydrop.app.models import Resource
from google.appengine.api import urlfetch
from google.appengine.ext import db
from drydrop.app.core.events import log_event

class VFS(object):
    """Virtual File System == filesystem abstraction for DryDrop"""
    def __init__(self):
        super(VFS, self).__init__()

    def fetch_resource_content(self, path):
        logging.warning('fetch_resource not implemented for %s', self.__class__.__name__)
        return None

    def fetch_file_timestamp(self, path):
        return None

    def get_resource(self, path):
        domain = os.environ['SERVER_NAME']
        resource = Resource.find(path=path, generation=self.settings.version, domain=domain)
        if resource is None:
            content = self.fetch_resource_content(path)
            created_on = self.fetch_file_timestamp(path)
            resource = Resource(path=path, content=content, generation=self.settings.version)
            if created_on is not None:
                resource.created_on = created_on
            try:
                length = len(resource.content)
            except:
                length = 0
            if length>0:
                log_event("Caching resource <code>%s</code> (%d bytes)" % (path, length))
            logging.debug("VFS: caching resource %s (%d bytes) for %s", path, length, domain)
            resource.domain = domain
            if content!=None:
              resource.save()
        try:
            length = len(resource.content)
        except:
            length = 0
        logging.debug("VFS: serving resource %s (%d bytes) for %s", path, length, domain)
        return resource

    def flush_resources(self, count = 1000):
        domain = os.environ['SERVER_NAME']
        deleted = Resource.clear(False, count, domain=domain)
        finished = deleted<count
        return finished, deleted

    def flush_resource(self, path):
        # purge all generations
        resources = Resource.all().filter("path =", path).filter("domain =", os.environ['SERVER_NAME']).fetch(1000)
        db.delete(resources)

    def get_all_resources(self):
        return Resource.all().filter("generation =", self.settings.version).filter("domain =", os.environ['SERVER_NAME']).fetch(1000)

class LocalVFS(VFS):
    """VFS for local development"""

    def __init__(self, settings):
        super(LocalVFS, self).__init__()
        self.settings = settings

    def get_resource(self, path):
        # check if file is fresh in cache
        resource = Resource.find(path=path, domain=os.environ['SERVER_NAME'])
        if resource is not None:
            stamp = self.fetch_file_timestamp(path)
            if stamp is not None and resource.created_on != stamp:
                logging.debug("VFS: file %s has been modified since last time => purged from cache", path)
                resource.delete()
        return super(LocalVFS, self).get_resource(path)

    def fetch_file_timestamp(self, path):
        root = self.settings.source
        if not root:
            return None
        filepath = os.path.join(root, path)
        try:
            s = os.stat(filepath)
        except:
            return None
        return datetime.datetime.fromtimestamp(s.st_mtime)

    def fetch_resource_content(self, path):
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

class GAEVFS(VFS):
    """VFS for production"""

    def __init__(self, settings):
        super(GAEVFS, self).__init__()
        self.settings = settings

    def fetch_resource_content(self, path):
        root = self.settings.source
        if not root:
            return None
        if not root.endswith('/'): root = root + "/"
        url = root + path
        params = []
        if self.settings.github_login:
            params.append("login=%s" % self.settings.github_login)
        if self.settings.github_token:
            params.append("token=%s" % self.settings.github_token)

        # note: params should be url-safe, so no need to escape here
        if len(params)>0:
            url = url + "?" + "&".join(params)

        response = urlfetch.fetch(url, follow_redirects=True)
        if response.status_code!=200:
            return None
        # HACK: if we get 200 with section referring to status404 treat it as 404, this is bug on github side
        #       see http://github.com/darwin/drydrop/issues/#issue/2 for more info
        if re.search(r'id="error" class="status404"', response.content):
            logging.warning("got bogus 404 response for %s", url)
            return None

        return response.content
