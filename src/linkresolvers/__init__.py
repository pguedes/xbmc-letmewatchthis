# -*- coding: UTF-8 -*-
'''
A module with a registry of link resolver objects.

The link resolver objects know how to resolve links from a tvshack.cc webpage into
playable streams. This may involve executing some HTTP requests to other websites.

This registry will maintain a list of known resolvers to make it easier to extend
the plugin with more supported video hosting websites.

Current list of link resolvers include:
 - tweety: can resolve 56.com, google video, tudou.com, veoh
 - youku: resolves youku links
 - megavideo: to resolve megavideo links. with support for megavideo premium accounts
 - movshare: resolves movshare and stagevu links
 - youtube: resolves youtube links
 - videoweed: resolves videoweed 
 - novamov: resolves novamov links
 - divxden: resolves divxden links
 
@author: pguedes 
'''
from plugin import PluginMovieItem
from utils.pluginsupport import select
import logging, utils.htmlutils as http, re
import megavideo, youku, tweety, movshare, youtube, videoweed, divxden, novamov, tvdex, veehd

log = logging.getLogger("linkresolvers")
resolvers = [megavideo, tweety, movshare, videoweed, youtube, youku, divxden]
resolversMap = {'56': tweety, 'google': tweety, 'tudou.com': tweety, 'veoh': tweety,
                'movshare': movshare, 'stagevu.com': movshare,
                'videoweed.com': videoweed, 
                'novamov.com': novamov,
                'youtube': youtube,
                'megavideo.com': megavideo,
                'veehd.com': veehd,
                'youku': youku,
                'tvdex.org': tvdex,
                'divxden': divxden}

def isSupported(source): 
  return resolversMap.has_key(source)

class UnresolvableSourceException(Exception):
  pass

class LoopingLinkResolver(object):
  """
  Loops thru all available link resolvers trying to resolve the file with each one. 
  """
  def resolve(self, page):
    '''
    Try to resolve a link into a playable stream url
    This will run through all registered linkresolvers trying one by one. The first one to succeed will return.
    @param page: the html of the webpage that resolvers can parse
    @return: a list of urls with playable streams
    '''
    for resolver in resolvers:
      try:
        log.debug("Attempting to resolve links with the '%s' resolver" % str(resolver))
        links = resolver.resolve(page)
        if links is not None and len(links) > 0:
          log.debug("Successfully resolved to: %s" % str(links));
          return links
      except:
        log.exception("Failed to resolve links with the '%s' resolver" % str(resolver))

class SourceList(object):
  def __init__(self, links, filterUnsupported=False):
    self.sources = {}
    for url, source in links:
      if isSupported(source) or not filterUnsupported:
        self.sources.setdefault(source, []).append(url)
        
  def selectSource(self, forceSourceSelection=False, autoplay=None):
    # if we need to resolve manually, we need individual links as choices
    sources = self.sources
    if forceSourceSelection:
      flattenedSources = {}
      for source, urls in self.sources.iteritems():
        for url in urls:
          flattenedSources["%s#%d" % (source, urls.index(url))] = [url]
      sources = flattenedSources
      
    log.debug("Found sources: %r"%sources)
    sourceNames = sources.keys()
    selected = self._selectSource(sourceNames, forceSourceSelection, autoplay)
    if selected >= 0:
      selectedsourcetype = sourceNames[selected]
      return Source(self.sources[selectedsourcetype], selectedsourcetype)
    
  def _selectSource(self, sources, forceSourceSelection, autoplay=None):
    if not sources:
      return -1
    elif len(sources) == 1:
      return 0
    else:
      if autoplay and not forceSourceSelection:
        for index in range(len(sources)):
          if sources[index] == autoplay:
            return index
       
      return select('Select source', sources)
 
    
class Source(object):
  """Represents a TvShack source and is able to resolve into url's for the player.
  A source maps to a host on the internet. For example, a source for a certain
  movie may be megavideo, and in this source a list of possibly resolvable links
  may exist. Resolving a source shall attempt to resolve each of these links
  returning the list of parts from the first one that successfully resolves."""
  def __init__(self, urls, type):
    log.warning("type: %s" % str(type))
    if not resolversMap.has_key(type):
      log.warning("No resolver found for type: %s" % str(type))
      self.__resolver = LoopingLinkResolver()
    else:
      self.__resolver = resolversMap[type]
    self.__sourceName = type
    self.__urls = urls
    
  def __resolveAlternate(self, url):
    log.debug("Listing parts at %s" % (url))
    links = self.__resolveLinks(url)
    if links:
      log.debug("Found part items: %s" % links)
      return links
    raise UnresolvableSourceException("No links found for '%s' on host '%s'" % (url, self.__sourceName))    
    
  def resolve(self):
    """Will resolve one of the available alternate versions of a playable item"""
    for url in self.__urls:
      try:
        return self.__resolveAlternate(url)
      except:
        log.exception("Failed to resolve alternate link")
    raise UnresolvableSourceException("No links found on %s" % (self.__sourceName))

  def __resolveLinks(self, url):
    return self.__resolver.resolve(http.get(url, True))
