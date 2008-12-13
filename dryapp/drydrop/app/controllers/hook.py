# -*- mode: python; coding: utf-8 -*-
import os
import datetime
import logging
import string
from drydrop_handler import DRY_ROOT
from drydrop.app.core.controller import BaseController
from drydrop.lib.json import json_parse
from drydrop.app.core.events import log_event

class HookController(BaseController):

    def github(self):
        payload = self.params.get('payload', None)
        if not payload:
            return
        
        data = json_parse(payload)
        logging.debug("Received github hook: %s", data)
        paths = []
        names = []
        for commit in data['commits']:
            author = commit['author']['email']
            try:
                names.index(author)
            except:
                names.append(author)
            try:
                paths.extend(commit['added'])
            except:
                pass
            try:
                paths.extend(commit['removed'])
            except:
                pass
            try:
                paths.extend(commit['modified'])
            except:
                pass
                
        log_event("Received github hook for commit %s (%d changes)" % (data['after'], len(paths)), string.join(names, ','))

        repo_url = data['repository']['url']
        branch = data['ref'].split('/').pop()
        
        root_url = "%s/raw/%s" % (repo_url, branch)
        if not root_url.endswith('/'):
            root_url = root_url + '/'
        source_url = self.handler.settings.source
        if not source_url.endswith('/'):
            source_url = source_url + '/'
        
        if not source_url.startswith(root_url):
            log_event("Source url '%s' is not affected by incoming changeset '%s'" % (source_url, root_url))
            logging.info("Source url '%s' is not affected by incoming changeset '%s'", source_url, root_url)
            return
        
        vfs = self.handler.vfs
        for path in paths:
            prefix = source_url[len(root_url):]
            if not path.beginswith(prefix):
                logging.warning("Unexpected: path %s, should begin with %s. Skipping file.", path, prefix)
            else:
                path = path[prefix:]
                logging.info("Flushing resource %s", path)
                vfs.flush_resource(path)