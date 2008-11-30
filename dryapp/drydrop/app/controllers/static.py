# -*- mode: python; coding: utf-8 -*-
import mimetypes
import os
import datetime
import glob
import logging
from drydrop_handler import DRY_ROOT
from drydrop.app.core.controller import BaseController
from drydrop.lib.utils import *

class StaticController(BaseController):
    
    def __init__(self, *arguments, **keywords):
        super(StaticController, self).__init__(*arguments, **keywords)
        self.more_data = None
        self.more_data_placeholder = None
        self.filter = None

    def static(self):
        self.base_path = os.path.join(DRY_ROOT, 'static')
        
    def after_action(self):
        path = self.params.get('path')
        more = None
        if self.more_data:
            more = self.more_data(self.base_path, path)
        return self.serve_static_file(self.base_path, path, more, self.more_data_placeholder, self.filter)