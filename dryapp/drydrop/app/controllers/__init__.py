# -*- mode: python; coding: utf-8 -*-
import sys
import drydrop.lib.walker
from drydrop.app.core.controller import AbstractController
drydrop.lib.walker.import_submodules(__file__, sys.modules[__name__], AbstractController)