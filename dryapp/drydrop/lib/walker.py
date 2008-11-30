# -*- mode: python; coding: utf-8 -*-
import os
import re
import inspect
import zipfile
from drydrop_handler import APP_ROOT
from drydrop.lib.utils import import_module

def cherrypick_classes_into_module(source, destination, common_ancestor=None):
    for key, item in source.__dict__.iteritems():
        if inspect.isclass(item):
            if common_ancestor is None or (issubclass(item, common_ancestor) and item!=common_ancestor):
                destination.__dict__[key] = item
            
def import_submodules(path, destination, ancestor=None):
    # want to import all classes from all *.py in directory pointed by path and put them into destination module
    #   optionaly also want to take only classes which are descendants of given ancestor
    #
    # classic path is in form: /here/is/some/project/dir/and/some/path/to/__init__.py
    # zip path is in form: something.zip/some/path/to/__init__.py
    # DRY_ROOT is path to project dir, where are located all zip files (it is not possible to extract this form zip path alone)
    #
    dir_path = os.path.dirname(path)
    m = re.match(r'^([^/]*?\.zip)/(.*)$', dir_path)
    if m:
        # zip case (we are on appspot.com)
        zipname = m.group(1)
        subpath = m.group(2)
        dot_module_path = subpath.replace('/', '.')
        module = zipname.split('.')[0]
        z = zipfile.ZipFile(os.path.join(APP_ROOT, zipname), 'r')
        for info in z.infolist():
            f = info.filename
            r = re.compile('^'+subpath+'/([^/]*)\.py$')
            x = re.match(r, f)
            if x:
                module_name =  x.group(1)
                if not module_name.startswith('__'):
                    module_selector = "%s.%s" % (dot_module_path, module_name)
                    module = import_module(module_selector)
                    cherrypick_classes_into_module(module, destination, ancestor)
    else:
        # classic case (local development box)
        for dirpath, dirnames, filenames in os.walk(dir_path):
            modules = [f.split('.')[0] for f in filenames if f.endswith('.py') and not f.startswith('__')]
            for module_name in modules:
                dot_module_path = dir_path[len(APP_ROOT)+1:].replace('/', '.')
                module_selector = "%s.%s" % (dot_module_path, module_name)
                module = import_module(module_selector)
                cherrypick_classes_into_module(module, destination, ancestor)