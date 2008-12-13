# -*- mode: python; coding: utf-8 -*-
import os
import datetime
import logging
from drydrop_handler import DRY_ROOT
from drydrop.app.core.controller import BaseController
from drydrop.lib.utils import *

class StaticController(BaseController):

    def static(self):
        self.base_path = os.path.join(DRY_ROOT, 'static')
        
    def after_action(self):
        path = self.params.get('path')
        return self.serve_static_file(self.base_path, path)