'''
Support for movshare and stagevu links

Created on Apr 6, 2010

@author: pguedes
'''
from resolverUtils import regexFinder, processSourcePage
import logging

log = logging.getLogger('movshare')

def resolve(page):
  finder = regexFinder('param name="src" value="(.+)"')
  streams = processSourcePage(page, finder)
  if len(streams) <= 0:
    finder = regexFinder('src="(http://.+?stagevu.com/v/.+/.+?.avi)"')
    streams = processSourcePage(page, finder)
  log.debug("Streams found: %s" % str(streams))
  return streams
  
