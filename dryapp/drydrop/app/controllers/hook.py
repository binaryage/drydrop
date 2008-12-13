# -*- mode: python; coding: utf-8 -*-
import os
import datetime
import logging
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
        logging.debug("received payload: %s", data)
        paths = []
        for commit in data['commits']:
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
                
        log_event("Received github hook for commit %s (%d changes)" % (data['after'], len(paths)))
        vfs = self.handler.vfs
        for path in paths:
            vfs.flush_resource(path)