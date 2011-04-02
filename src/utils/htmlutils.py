# -*- coding: UTF-8 -*-
import re, urllib2
import logging

log = logging.getLogger("htmlutils")

def get(url, ajax=False, cleanup=False, data=None, returnResponse=False, extraHeaders=None):
  '''
  Load a webpage from with an HTTP request like a browser would do
  @param ajax: if True, will add header to identify to server as an XMLHttpRequest (from a browser)
  @param cleanup: if True, data will be cleaned up before returning
  @param data: data to be POSTed on the request
  @param returnResponse: if True, will return the response object before reading instead of data read
  '''
  target = getTarget(url)
  req = urllib2.Request(target)
  req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7')
  if ajax:
    req.add_header('X-Requested-With', 'XMLHttpRequest')
  if extraHeaders:
    for header, headerval in extraHeaders.iteritems():
      req.add_header(header, headerval)
  log.debug("Getting target '%s' (original: %s)" % (target, url))
  response = urllib2.urlopen(req, data)
  if returnResponse:
    return response
  html = response.read()
  response.close()
  if cleanup:
    html = cleanHtml(html)
  return html
 
def getTarget(url):
  target = url
  if url.find('http://') < 0:
    target = "http://www.letmewatchthis.com" + url
  return target
 
def cleanHtml(html):
  '''
  Cleanup html
  @param html: original HTML to be cleaned up
  '''
  clean = re.sub('&eacute;', 'ea', html)
  clean = re.sub('&amp;', '&', clean)
  clean = re.sub('&quot;', '', clean)
  clean = re.sub('&nbsp;<font class=".+?">.+?</font>', '', clean)
  clean = re.sub('&#x22;', '', clean)
  return clean
