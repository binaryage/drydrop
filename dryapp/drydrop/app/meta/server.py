#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# taken from GAE SDK 1.1.7 modified by Antonin Hildebrand

"""Pure-Python application server for testing applications locally.

Given a port and the paths to a valid application directory (with an 'app.yaml'
file), the external library directory, and a relative URL to use for logins,
creates an HTTP server that can be used to test an application locally. Uses
stubs instead of actual APIs when SetupStubs() is called first.

Example:
  root_path = '/path/to/application/directory'
  login_url = '/login'
  port = 8080
  template_dir = '/path/to/appserver/templates'
  server = dev_appserver.CreateServer(root_path, login_url, port, template_dir)
  server.serve_forever()
"""


import cStringIO
import cgi
import email.Utils
import errno
import httplib
import imp
import inspect
import itertools
import locale
import logging
import mimetools
import mimetypes
import os
import pickle
import pprint
import random

import re
import sre_compile
import sre_constants
import sre_parse

import mimetypes
import socket
import sys
import time
import traceback
import types
import urlparse
import urllib

import google
from google.pyglib import gexcept

from drydrop.app.meta import appinfo
from drydrop.app.meta import yaml_errors
from google.appengine.api import users
from drydrop_handler import ReadDataFile

FILE_MISSING_EXCEPTIONS = frozenset([errno.ENOENT, errno.ENOTDIR])

MAX_URL_LENGTH = 2047

for ext, mime_type in (('.asc', 'text/plain'),
                       ('.diff', 'text/plain'),
                       ('.csv', 'text/comma-separated-values'),
                       ('.rss', 'application/rss+xml'),
                       ('.text', 'text/plain'),
                       ('.wbmp', 'image/vnd.wap.wbmp')):
  mimetypes.add_type(mime_type, ext)

class Error(Exception):
  """Base-class for exceptions in this module."""

class InvalidAppConfigError(Error):
  """The supplied application configuration file is invalid."""

class AppConfigNotFoundError(Error):
  """Application configuration file not found."""

class TemplatesNotLoadedError(Error):
  """Templates for the debugging console were not loaded."""


def SplitURL(relative_url):
  """Splits a relative URL into its path and query-string components.

  Args:
    relative_url: String containing the relative URL (often starting with '/')
      to split. Should be properly escaped as www-form-urlencoded data.

  Returns:
    Tuple (script_name, query_string) where:
      script_name: Relative URL of the script that was accessed.
      query_string: String containing everything after the '?' character.
  """
  scheme, netloc, path, query, fragment = urlparse.urlsplit(relative_url)
  return path, query


class URLDispatcher(object):
  """Base-class for handling HTTP requests."""

  def Dispatch(self,
               relative_url,
               path,
               headers,
               infile,
               outfile,
               base_env_dict=None):
    """Dispatch and handle an HTTP request.

    base_env_dict should contain at least these CGI variables:
      REQUEST_METHOD, REMOTE_ADDR, SERVER_SOFTWARE, SERVER_NAME,
      SERVER_PROTOCOL, SERVER_PORT

    Args:
      relative_url: String containing the URL accessed.
      path: Local path of the resource that was matched; back-references will be
        replaced by values matched in the relative_url. Path may be relative
        or absolute, depending on the resource being served (e.g., static files
        will have an absolute path; scripts will be relative).
      headers: Instance of mimetools.Message with headers from the request.
      infile: File-like object with input data from the request.
      outfile: File-like object where output data should be written.
      base_env_dict: Dictionary of CGI environment parameters if available.
        Defaults to None.
    """
    raise NotImplementedError


class URLMatcher(object):
  """Matches an arbitrary URL using a list of URL patterns from an application.

  Each URL pattern has an associated URLDispatcher instance and path to the
  resource's location on disk. See AddURL for more details. The first pattern
  that matches an inputted URL will have its associated values returned by
  Match().
  """

  def __init__(self):
    """Initializer."""
    self._url_patterns = []

  def AddURL(self, regex, dispatcher, path, requires_login, admin_only):
    """Adds a URL pattern to the list of patterns.

    If the supplied regex starts with a '^' or ends with a '$' an
    InvalidAppConfigError exception will be raised. Start and end symbols
    and implicitly added to all regexes, meaning we assume that all regexes
    consume all input from a URL.

    Args:
      regex: String containing the regular expression pattern.
      dispatcher: Instance of URLDispatcher that should handle requests that
        match this regex.
      path: Path on disk for the resource. May contain back-references like
        r'\1', r'\2', etc, which will be replaced by the corresponding groups
        matched by the regex if present.
      requires_login: True if the user must be logged-in before accessing this
        URL; False if anyone can access this URL.
      admin_only: True if the user must be a logged-in administrator to
        access the URL; False if anyone can access the URL.
    """
    if not isinstance(dispatcher, URLDispatcher):
      raise TypeError, 'dispatcher must be a URLDispatcher sub-class'

    if regex.startswith('^') or regex.endswith('$'):
      raise InvalidAppConfigError, 'regex starts with "^" or ends with "$"'

    adjusted_regex = '^%s$' % regex

    try:
      url_re = re.compile(adjusted_regex)
    except re.error, e:
      raise InvalidAppConfigError, 'regex invalid: %s' % e

    match_tuple = (url_re, dispatcher, path, requires_login, admin_only)
    self._url_patterns.append(match_tuple)

  def Match(self,
            relative_url,
            split_url=SplitURL):
    """Matches a URL from a request against the list of URL patterns.

    The supplied relative_url may include the query string (i.e., the '?'
    character and everything following).

    Args:
      relative_url: Relative URL being accessed in a request.

    Returns:
      Tuple (dispatcher, matched_path, requires_login, admin_only), which are
      the corresponding values passed to AddURL when the matching URL pattern
      was added to this matcher. The matched_path will have back-references
      replaced using values matched by the URL pattern. If no match was found,
      dispatcher will be None.
    """
    adjusted_url, query_string = split_url(relative_url)

    for url_tuple in self._url_patterns:
      url_re, dispatcher, path, requires_login, admin_only = url_tuple
      logging.debug("URL match: %s %s", url_re.pattern, adjusted_url)
      the_match = url_re.match(adjusted_url)

      if the_match:
        adjusted_path = the_match.expand(path)
        return dispatcher, adjusted_path, requires_login, admin_only

    return None, None, None, None

  def GetDispatchers(self):
    """Retrieves the URLDispatcher objects that could be matched.

    Should only be used in tests.

    Returns:
      A set of URLDispatcher objects.
    """
    return set([url_tuple[1] for url_tuple in self._url_patterns])


def GetUserInfo():
    user = users.get_current_user()
    if not user:
        return (None, False)
    return (user.email(), users.is_current_user_admin())
    
def LoginRedirect(login_url,
                  hostname,
                  port,
                  relative_url,
                  outfile):
  # dest_url = "http://%s:%s%s" % (hostname, port, relative_url)
  # redirect_url = 'http://%s:%s%s?%s=%s' % (hostname,
  #                                          port,
  #                                          login_url,
  #                                          CONTINUE_PARAM,
  #                                          urllib.quote(dest_url))
  # outfile.write('Status: 302 Requires login\r\n')
  # outfile.write('Location: %s\r\n\r\n' % redirect_url)
  pass

class MatcherDispatcher(URLDispatcher):
  """Dispatcher across multiple URLMatcher instances."""

  def __init__(self,
               login_url,
               url_matchers,
               get_user_info=GetUserInfo,
               login_redirect=LoginRedirect):
    """Initializer.

    Args:
      login_url: Relative URL which should be used for handling user logins.
      url_matchers: Sequence of URLMatcher objects.
      get_user_info, login_redirect: Used for dependency injection.
    """
    self._login_url = login_url
    self._url_matchers = tuple(url_matchers)
    self._get_user_info = get_user_info
    self._login_redirect = login_redirect

  def Dispatch(self,
               relative_url,
               path,
               headers,
               infile,
               outfile,
               base_env_dict=None):
    """Dispatches a request to the first matching dispatcher.

    Matchers are checked in the order they were supplied to the constructor.
    If no matcher matches, a 404 error will be written to the outfile. The
    path variable supplied to this method is ignored.
    """
    email, admin = self._get_user_info()

    for matcher in self._url_matchers:
      dispatcher, matched_path, requires_login, admin_only = matcher.Match(relative_url)
      if dispatcher is None:
        continue

      logging.debug('Matched "%s" to %s with path %s',
                    relative_url, dispatcher, matched_path)

      if (requires_login or admin_only) and not email:
        logging.debug('Login required, redirecting user')
        self._login_redirect(
          self._login_url,
          base_env_dict['SERVER_NAME'],
          base_env_dict['SERVER_PORT'],
          relative_url,
          outfile)
      elif admin_only and not admin:
        outfile.write('Status: %d Not authorized\r\n'
                      '\r\n'
                      'Current logged in user %s is not '
                      'authorized to view this page.'
                      % (httplib.FORBIDDEN, email))
      else:
        dispatcher.Dispatch(relative_url,
                            matched_path,
                            headers,
                            infile,
                            outfile,
                            base_env_dict=base_env_dict)

      return

    outfile.write('Status: %d URL did not match\r\n'
                  '\r\n'
                  'Not found error: %s did not match any patterns '
                  'in application configuration.'
                  % (httplib.NOT_FOUND, relative_url))

def ExecuteCGI(root_path,
               handler_path,
               cgi_path,
               env,
               infile,
               outfile,
               module_dict,
               exec_script):
  """Executes Python file in this process as if it were a CGI.

  Does not return an HTTP response line. CGIs should output headers followed by
  the body content.

  The modules in sys.modules should be the same before and after the CGI is
  executed, with the specific exception of encodings-related modules, which
  cannot be reloaded and thus must always stay in sys.modules.

  Args:
    root_path: Path to the root of the application.
    handler_path: CGI path stored in the application configuration (as a path
      like 'foo/bar/baz.py'). May contain $PYTHON_LIB references.
    cgi_path: Absolute path to the CGI script file on disk.
    env: Dictionary of environment variables to use for the execution.
    infile: File-like object to read HTTP request input data from.
    outfile: FIle-like object to write HTTP response data to.
    module_dict: Dictionary in which application-loaded modules should be
      preserved between requests. This removes the need to reload modules that
      are reused between requests, significantly increasing load performance.
      This dictionary must be separate from the sys.modules dictionary.
    exec_script: Used for dependency injection.
  """
  # old_module_dict = sys.modules.copy()
  # old_builtin = __builtin__.__dict__.copy()
  # old_argv = sys.argv
  # old_stdin = sys.stdin
  # old_stdout = sys.stdout
  # old_env = os.environ.copy()
  # old_cwd = os.getcwd()
  # old_file_type = types.FileType
  # reset_modules = False
  # 
  # try:
  #   ClearAllButEncodingsModules(sys.modules)
  #   sys.modules.update(module_dict)
  #   sys.argv = [cgi_path]
  #   sys.stdin = infile
  #   sys.stdout = outfile
  #   os.environ.clear()
  #   os.environ.update(env)
  #   before_path = sys.path[:]
  #   cgi_dir = os.path.normpath(os.path.dirname(cgi_path))
  #   root_path = os.path.normpath(os.path.abspath(root_path))
  #   if cgi_dir.startswith(root_path + os.sep):
  #     os.chdir(cgi_dir)
  #   else:
  #     os.chdir(root_path)
  # 
  #   hook = HardenedModulesHook(sys.modules)
  #   sys.meta_path = [hook]
  #   if hasattr(sys, 'path_importer_cache'):
  #     sys.path_importer_cache.clear()
  # 
  #   __builtin__.file = FakeFile
  #   __builtin__.open = FakeFile
  #   types.FileType = FakeFile
  # 
  #   __builtin__.buffer = NotImplementedFakeClass
  # 
  #   logging.debug('Executing CGI with env:\n%s', pprint.pformat(env))
  #   try:
  #     reset_modules = exec_script(handler_path, cgi_path, hook)
  #   except SystemExit, e:
  #     logging.debug('CGI exited with status: %s', e)
  #   except:
  #     reset_modules = True
  #     raise
  # 
  # finally:
  #   sys.meta_path = []
  #   sys.path_importer_cache.clear()
  # 
  #   _ClearTemplateCache(sys.modules)
  # 
  #   module_dict.update(sys.modules)
  #   ClearAllButEncodingsModules(sys.modules)
  #   sys.modules.update(old_module_dict)
  # 
  #   __builtin__.__dict__.update(old_builtin)
  #   sys.argv = old_argv
  #   sys.stdin = old_stdin
  #   sys.stdout = old_stdout
  # 
  #   sys.path[:] = before_path
  # 
  #   os.environ.clear()
  #   os.environ.update(old_env)
  #   os.chdir(old_cwd)
  # 
  #   types.FileType = old_file_type
  pass


def SetupEnvironment(cgi_path,
                       relative_url,
                       headers,
                       split_url=SplitURL,
                       get_user_info=GetUserInfo):
    """Sets up environment variables for a CGI.

    Args:
      cgi_path: Full file-system path to the CGI being executed.
      relative_url: Relative URL used to access the CGI.
      headers: Instance of mimetools.Message containing request headers.
      split_url, get_user_info: Used for dependency injection.

    Returns:
      Dictionary containing CGI environment variables.
    """
    # env = DEFAULT_ENV.copy()
    # 
    # script_name, query_string = split_url(relative_url)
    # 
    # env['SCRIPT_NAME'] = ''
    # env['QUERY_STRING'] = query_string
    # env['PATH_INFO'] = urllib.unquote(script_name)
    # env['PATH_TRANSLATED'] = cgi_path
    # env['CONTENT_TYPE'] = headers.getheader('content-type', 'application/x-www-form-urlencoded')
    # env['CONTENT_LENGTH'] = headers.getheader('content-length', '')
    # 
    # email, admin = get_user_info()
    # env['USER_EMAIL'] = email
    # if admin:
    #   env['USER_IS_ADMIN'] = '1'
    # 
    # for key in headers:
    #   if key in _IGNORE_HEADERS:
    #     continue
    #   adjusted_name = key.replace('-', '_').upper()
    #   env['HTTP_' + adjusted_name] = ', '.join(headers.getheaders(key))

    return {}

class CGIDispatcher(URLDispatcher):
  """Dispatcher that executes Python CGI scripts."""

  def __init__(self,
               module_dict,
               root_path,
               path_adjuster,
               setup_env=SetupEnvironment,
               exec_cgi=ExecuteCGI):
    """Initializer.

    Args:
      module_dict: Dictionary in which application-loaded modules should be
        preserved between requests. This dictionary must be separate from the
        sys.modules dictionary.
      path_adjuster: Instance of PathAdjuster to use for finding absolute
        paths of CGI files on disk.
      setup_env, exec_cgi, create_logging_handler: Used for dependency
        injection.
    """
    self._module_dict = module_dict
    self._root_path = root_path
    self._path_adjuster = path_adjuster
    self._setup_env = setup_env
    self._exec_cgi = exec_cgi

  def Dispatch(self,
               relative_url,
               path,
               headers,
               infile,
               outfile,
               base_env_dict=None):
      """Dispatches the Python CGI."""
      env = {}
      cgi_path = self._path_adjuster.AdjustPath(path)
      env.update(self._setup_env(cgi_path, relative_url, headers))
      self._exec_cgi(self._root_path,
                     path,
                     cgi_path,
                     env,
                     infile,
                     outfile,
                     self._module_dict,
                     None)

  def __str__(self):
    """Returns a string representation of this dispatcher."""
    return 'CGI dispatcher'


class PathAdjuster(object):
  """Adjusts application file paths to paths relative to the application or
  external library directories."""

  def __init__(self, root_path):
    """Initializer.

    Args:
      root_path: Path to the root of the application running on the server.
    """
    self._root_path = os.path.abspath(root_path)

  def AdjustPath(self, path):
    """Adjusts application file path to paths relative to the application or
    external library directories.

    Handler paths that start with $PYTHON_LIB will be converted to paths
    relative to the google directory.

    Args:
      path: File path that should be adjusted.

    Returns:
      The adjusted path.
    """
    if path.startswith('./'):
        path = path[2:]
    if path.startswith('/'):
        path = path[1:]
    return path


class StaticFileConfigMatcher(object):
  """Keeps track of file/directory specific application configuration.

  Specifically:
  - Computes mime type based on URLMap and file extension.
  - Decides on cache expiration time based on URLMap and default expiration.

  To determine the mime type, we first see if there is any mime-type property
  on each URLMap entry. If non is specified, we use the mimetypes module to
  guess the mime type from the file path extension, and use
  application/octet-stream if we can't find the mimetype.
  """

  def __init__(self,
               url_map_list,
               path_adjuster,
               default_expiration):
    """Initializer.

    Args:
      url_map_list: List of appinfo.URLMap objects.
        If empty or None, then we always use the mime type chosen by the
        mimetypes module.
      path_adjuster: PathAdjuster object used to adjust application file paths.
      default_expiration: String describing default expiration time for browser
        based caching of static files.  If set to None this disallows any
        browser caching of static content.
    """
    if default_expiration is not None:
      self._default_expiration = appinfo.ParseExpiration(default_expiration)
    else:
      self._default_expiration = None

    self._patterns = []

    if url_map_list:
      for entry in url_map_list:
        handler_type = entry.GetHandlerType()
        if handler_type not in (appinfo.STATIC_FILES, appinfo.STATIC_DIR):
          continue

        if handler_type == appinfo.STATIC_FILES:
          regex = entry.upload + '$'
        else:
          path = entry.static_dir
          if path[-1] == '/':
            path = path[:-1]
          regex = re.escape(path) + r'/(.*)'

        try:
          path_re = re.compile(regex)
        except re.error, e:
          raise InvalidAppConfigError('regex %s does not compile: %s' %
                                      (regex, e))

        if self._default_expiration is None:
          expiration = 0
        elif entry.expiration is None:
          expiration = self._default_expiration
        else:
          expiration = appinfo.ParseExpiration(entry.expiration)

        self._patterns.append((path_re, entry.mime_type, expiration))

  def GetMimeType(self, path):
    """Returns the mime type that we should use when serving the specified file.

    Args:
      path: String containing the file's path relative to the app.

    Returns:
      String containing the mime type to use. Will be 'application/octet-stream'
      if we have no idea what it should be.
    """
    for (path_re, mime_type, expiration) in self._patterns:
      if mime_type is not None:
        the_match = path_re.match(path)
        if the_match:
          return mime_type

    filename, extension = os.path.splitext(path)
    return mimetypes.types_map.get(extension, 'application/octet-stream')

  def GetExpiration(self, path):
    """Returns the cache expiration duration to be users for the given file.

    Args:
      path: String containing the file's path relative to the app.

    Returns:
      Integer number of seconds to be used for browser cache expiration time.
    """
    for (path_re, mime_type, expiration) in self._patterns:
      the_match = path_re.match(path)
      if the_match:
        return expiration

    return self._default_expiration or 0

class FileDispatcher(URLDispatcher):
  """Dispatcher that reads data files from disk."""

  def __init__(self,
               path_adjuster,
               static_file_config_matcher,
               vfs,
               read_data_file=ReadDataFile):
    """Initializer.

    Args:
      path_adjuster: Instance of PathAdjuster to use for finding absolute
        paths of data files on disk.
      static_file_config_matcher: StaticFileConfigMatcher object.
      read_data_file: Used for dependency injection.
    """
    self._path_adjuster = path_adjuster
    self._static_file_config_matcher = static_file_config_matcher
    self._read_data_file = read_data_file
    self._vfs = vfs

  def Dispatch(self,
               relative_url,
               path,
               headers,
               infile,
               outfile,
               base_env_dict=None):
    """Reads the file and returns the response status and data."""
    SPACE_MARKER = '--~!-real-space-marker-!~--'
    path = path.replace('\\ ', SPACE_MARKER)
    parts = path.split(' ')
    c = 0
    for part in parts:
        c = c + 1
        new_path = part.replace(SPACE_MARKER, ' ')
        full_path = self._path_adjuster.AdjustPath(new_path)
        status, data, created_on = self._read_data_file(full_path, self._vfs)
        if status==httplib.OK or c==len(parts):
            content_type = self._static_file_config_matcher.GetMimeType(new_path)
            expiration = self._static_file_config_matcher.GetExpiration(new_path)

            outfile.write('Status: %d\r\n' % status)
            outfile.write('Content-Type: %s\r\n' % content_type)
            
            # Send a Last-Modified header
            HTTP_date = created_on.strftime('%a, %d %b %Y %H:%M:%S GMT')
            outfile.write('Last-Modified: %s\r\n' % HTTP_date)
            
            if expiration:
              outfile.write('Expires: %s\r\n'
                            % email.Utils.formatdate(time.time() + expiration,
                                                     usegmt=True))
              outfile.write('Cache-Control: public, max-age=%i\r\n' % expiration)
            outfile.write('\r\n')
            outfile.write(data)
            return

  def __str__(self):
    """Returns a string representation of this dispatcher."""
    return 'File dispatcher'


def RewriteResponse(response_file):
  """Interprets server-side headers and adjusts the HTTP response accordingly.

  Handles the server-side 'status' header, which instructs the server to change
  the HTTP response code accordingly. Handles the 'location' header, which
  issues an HTTP 302 redirect to the client. Also corrects the 'content-length'
  header to reflect actual content length in case extra information has been
  appended to the response body.

  If the 'status' header supplied by the client is invalid, this method will
  set the response to a 500 with an error message as content.

  Args:
    response_file: File-like object containing the full HTTP response including
      the response code, all headers, and the request body.

  Returns:
    Tuple (status_code, status_message, header, body) where:
      status_code: Integer HTTP response status (e.g., 200, 302, 404, 500)
      status_message: String containing an informational message about the
        response code, possibly derived from the 'status' header, if supplied.
      header: String containing the HTTP headers of the response, without
        a trailing new-line (CRLF).
      body: String containing the body of the response.
  """
  headers = mimetools.Message(response_file)

  response_status = '%d OK' % httplib.OK
  # 
  location_value = headers.getheader('location')
  status_value = headers.getheader('status')
  if status_value:
    response_status = status_value
    del headers['status']
  elif location_value:
    response_status = '%d Redirecting' % httplib.FOUND
  # 
  # if not 'Cache-Control' in headers:
  #   headers['Cache-Control'] = 'no-cache'

  status_parts = response_status.split(' ', 1)
  status_code, status_message = (status_parts + [''])[:2]
  try:
    status_code = int(status_code)
  except ValueError:
    status_code = 500
    body = 'Error: Invalid "status" header value returned.'
  else:
    body = response_file.read()

  # headers['content-length'] = str(len(body))
  # 
  header_list = []
  for header in headers.headers:
    header = header.rstrip('\n')
    header = header.rstrip('\r')
    header_list.append(header)

  return status_code, status_message, header_list, body


def CreateURLMatcherFromMaps(root_path,
                             url_map_list,
                             module_dict,
                             default_expiration,
                             vfs,
                             create_url_matcher=URLMatcher,
                             create_cgi_dispatcher=CGIDispatcher,
                             create_file_dispatcher=FileDispatcher,
                             create_path_adjuster=PathAdjuster,
                             normpath=os.path.normpath):
  """Creates a URLMatcher instance from URLMap.

  Creates all of the correct URLDispatcher instances to handle the various
  content types in the application configuration.

  Args:
    root_path: Path to the root of the application running on the server.
    url_map_list: List of appinfo.URLMap objects to initialize this
      matcher with. Can be an empty list if you would like to add patterns
      manually.
    module_dict: Dictionary in which application-loaded modules should be
      preserved between requests. This dictionary must be separate from the
      sys.modules dictionary.
    default_expiration: String describing default expiration time for browser
      based caching of static files.  If set to None this disallows any
      browser caching of static content.
    create_url_matcher, create_cgi_dispatcher, create_file_dispatcher,
    create_path_adjuster: Used for dependency injection.

  Returns:
    Instance of URLMatcher with the supplied URLMap objects properly loaded.
  """
  url_matcher = create_url_matcher()
  path_adjuster = create_path_adjuster(root_path)
  cgi_dispatcher = create_cgi_dispatcher(module_dict, root_path, path_adjuster)
  file_dispatcher = create_file_dispatcher(path_adjuster,
      StaticFileConfigMatcher(url_map_list, path_adjuster, default_expiration), vfs)

  for url_map in url_map_list:
    admin_only = url_map.login == appinfo.LOGIN_ADMIN
    requires_login = url_map.login == appinfo.LOGIN_REQUIRED or admin_only

    handler_type = url_map.GetHandlerType()
    if handler_type == appinfo.HANDLER_SCRIPT:
      dispatcher = cgi_dispatcher
    elif handler_type in (appinfo.STATIC_FILES, appinfo.STATIC_DIR):
      dispatcher = file_dispatcher
    else:
      raise InvalidAppConfigError('Unknown handler type "%s"' % handler_type)

    regex = url_map.url
    path = url_map.GetHandler()
    if handler_type == appinfo.STATIC_DIR:
      if regex[-1] == r'/':
        regex = regex[:-1]
      if path[-1] == os.path.sep:
        path = path[:-1]
      regex = '/'.join((re.escape(regex), '(.*)'))
      if os.path.sep == '\\':
        backref = r'\\1'
      else:
        backref = r'\1'
      path = (normpath(path).replace('\\', '\\\\') +
              os.path.sep + backref)

    url_matcher.AddURL(regex,
                       dispatcher,
                       path,
                       requires_login, admin_only)

  return url_matcher


def ParseAppConfig(root_path,
                  config_source,
                  vfs,
                  static_caching=True,
                  create_matcher=CreateURLMatcherFromMaps):
    config = appinfo.LoadSingleAppInfo(config_source)

    if static_caching:
      if config.default_expiration:
        default_expiration = config.default_expiration
      else:
        default_expiration = '0'
    else:
      default_expiration = None

    matcher = create_matcher(root_path,
                             config.handlers,
                             {},
                             default_expiration,
                             vfs)

    return (config, matcher)
