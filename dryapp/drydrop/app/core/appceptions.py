# -*- mode: python; coding: utf-8 -*-
import exceptions

class PageException(exceptions.Exception):
    pass

class PageError(PageException):
    def __init__(self, errno, msg):
        self.args = (errno, msg)
        self.errno = errno
        self.errmsg = msg

class PageRedirect(PageException):
    def __init__(self, url):
        self.args = (url)
        self.url = url
        
class DownloadError(PageException):
    def __init__(self, msg):
        self.args = (msg)
        self.errmsg = msg