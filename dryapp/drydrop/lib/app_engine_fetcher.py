from openid import fetchers
from google.appengine.api import urlfetch
import logging

class AppEngineFetcher(fetchers.HTTPFetcher):
  """An HTTPFetcher subclass that uses Google App Engine's urlfetch module.
  """
  def fetch(self, url, body=None, headers=None):
    if not fetchers._allowedURL(url):
      raise ValueError('Bad URL scheme: %r' % (url,))
    
    if not headers:
      headers = {}

    if body:
      method = urlfetch.POST
      headers['Content-type'] = 'application/x-www-form-urlencoded' 
    else:
      method = urlfetch.GET

    count = 0
    resp = urlfetch.fetch(url, body, method, headers=headers)

    # follow redirects for a while
    while resp.status_code in [301,302]:
      count += 1
      if count >= 3:
        raise Exception('too many redirects')

      if resp.headers.has_key('location'):
        url = resp.headers['location']
      elif resp.headers.has_key('Location'):
        url = resp.headers['Location']
      else:
        raise Exception('Could not find location in headers: %r' % (resp.headers,))
      
      resp = urlfetch.fetch(url, body, method, headers=headers)

    # normalize headers
    for key, val in resp.headers.items():
      resp.headers[key.lower()] = val

    return fetchers.HTTPResponse(url, resp.status_code, resp.headers, resp.content)