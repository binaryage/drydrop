# -*- mode: python; coding: utf-8 -*-
from drydrop.app.core.controller import BaseController
import logging

class WelcomeController(BaseController):

    def index(self):
        self.render_view('welcome/index.html')
