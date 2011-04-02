'''
Created on May 31, 2010

@author: pedro
'''
import logging, re, utils.htmlutils as http

log = logging.getLogger("linkresolvers")

def regexFinder(regex):
  """Create a finder that returns all matches for a regex"""
  def finder(page):
    found = re.compile(regex).findall(page)
    log.debug("Found links: %s" % str(found))
    return found
  return finder

def processSourcePage(page, processor):
  """Will call the processor with the first src="(.+?)" page found"""
  log.debug("frame page: %s" % str(page))
  url = re.compile('src="(http://.+?)"').findall(page)
  log.debug("Found stream page urls: %s" % str(url))
  url = url[0].replace('&amp;', '&')
  html = http.get(url)
  log.debug("Loaded stream page: %s" % str(html))
  return processor(html)

