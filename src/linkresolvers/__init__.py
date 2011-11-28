# -*- coding: UTF-8 -*-
'''A module about transforming a playable item selection into urls that can be played by XBMC's player.

This module contains three main abstractions:
 - source: a website that hosts the actual media we want to play (@see: Source)
 - source list selection: how do we select the source to play (preferred source, manual selection) (@see: SourceList)
 - link resolvers: implementation of specific strategies to grab the actual media links from the sources (@see: LinkResolver)

The Source class provides an interface for this module. 
A source is one of the media hosting websites which is directly tied to a link resolver.
By instantiating a Source, you get an object with a 'resolve' method that will call the linkresolver for that website and return 
the collected links or raise an exception if it cannot.

The SourceList class implements the logic of selecting a Source out of a set of currently available ones.

The LinkResolver objects know how to resolve links from a webpage into playable streams. 
This may involve executing some HTTP requests to other websites.

This module maintains a registry of known resolvers to make it easier to extend the plugin with more supported hosting websites.

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
import logging, re

# TODO fix the old modules to properly implement LinkResolver.. for now only putlocker
#import megavideo, youku, tweety, movshare, youtube, videoweed, divxden, novamov, tvdex, veehd, putlocker

#resolvers = [megavideo, tweety, movshare, videoweed, youtube, youku, divxden, putlocker]
#resolversMap = {'56': tweety, 'google': tweety, 'tudou.com': tweety, 'veoh': tweety,
#                'movshare': movshare, 'stagevu.com': movshare,
#                'videoweed.com': videoweed,
#                'novamov.com': novamov,
#                'youtube': youtube,
#                'megavideo.com': megavideo,
#                'veehd.com': veehd,
#                'youku': youku,
#                'tvdex.org': tvdex,
#                'putlocker': putlocker,
#                'divxden': divxden}

from utils import htmlutils, notification
from linkresolvers.putlocker import PutLockerLinkResolver
putlocker = PutLockerLinkResolver()
resolvers = [putlocker]
resolversMap = {'putlocker': putlocker}

log = logging.getLogger("linkresolvers")

def isSupported(source):
    '''checks if a certain source is supported by the curent linkresolvers module configuration.
    @param source: the source to test if we can resolve links from
    @return: true if the source is supported, false otherwise'''
    return resolversMap.has_key(source)

class UnresolvableSourceException(Exception):
    '''exception raised when a source's links cannot be resolved'''
    pass

class NoSourceSelectedException(Exception):
    '''exception raised when a source cannot be selected'''
    pass

class LinkResolver(object):
    '''interface for link resolver objects
    NOTE: python does not have interfaces and most of the code is old and does not implement this. for documentation purposes'''
    def resolve(self, url):
        '''resolve the links on the page
        @param url: the url of the page to get links for
        @return: the list of resolved playable urls for XBMC's player'''

class LoopingLinkResolver(LinkResolver):
    '''a fallback LinkResolver that will simply loop through all available LinkResovlers and attempt one-by-one to 
    resolve the links returning from the first one that succeeds, or not at all'''
    def resolve(self, url):
        '''Try to resolve a link into a playable stream url
        This will run through all registered linkresolvers trying one by one. The first one to succeed will return.
        @param url: the url of the webpage that resolvers can parse
        @return: a list of urls with playable streams'''
        for resolver in resolvers:
            try:
                log.debug("Attempting to resolve links with the '%s' resolver" % str(resolver))
                links = resolver.resolve(url)
                if links is not None and len(links) > 0:
                    log.debug("Successfully resolved to: %s" % str(links));
                    return links
            except:
                log.exception("Failed to resolve links with the '%s' resolver" % str(resolver))

class SourceList(object):
    '''This class encapsulates the logic of selection of a source from a list of available one.
    Each media target (a movie, or an episode of a show), is tipically hosted on multiple source sites (hosters)
    @see: selectSource'''

    def __init__(self, links, filterUnsupported=False):
        '''create a new SourceList to select from a list of sources.
        @param links: a list of tuples with (url, name) of sources to use as choices for source selection
        @param filterUnsupported: if sources that are not supported should be excluded from the options'''
        self.sources = {}
        for url, source in links:
            if isSupported(source) or not filterUnsupported:
                self.sources.setdefault(source, []).append(url)


    def selectSource(self, forceSourceSelection=False, autoplay=None):
        '''selects one out of the available sources.
        If a selection is envolved will either autoselect the autoplay source or allow the user to choose.
        @param forceSourceSelection: if true the user will allways have to choose the source manually
        @param autoplay: the preferred source to auto-select if choosing is involved
        @return: the selected Source
        @raise NoSourceSelectedException: raised when no source was selected'''
        log.debug("Selecting from sources: %r" % self.sources)

        sources = self.sources
        if forceSourceSelection:
            sources = self.__getNumberedSources()

        sourceNames = sources.keys()

        selected = self._selectSource(sourceNames, forceSourceSelection, autoplay)
        if selected >= 0:
            selectedsourcetype = sourceNames[selected]
            return Source(sources[selectedsourcetype], selectedsourcetype)

        raise NoSourceSelectedException('no source selected to play')

    def _selectSource(self, sources, forceSourceSelection, autoplay=None):
        '''select one source out of a list of possible.
        Automatically selects:
         - if there is only one source, that one
         - if there is an option and one of the options is the autoplay one, then that
        Otherwise delegates selection to the user via the pluginsupport.select() method.
        @param sources: the list of possible sources
        @param forceSourceSelection: if true and there is an option it will be left for the user
        @param autoplay: the preferred selection to auto-select if there is an option and we do not want to force the user to select
        @return: the selected source (@see: Source)'''
        if not sources:
            return - 1
        elif len(sources) == 1:
            return 0
        elif autoplay and not forceSourceSelection:
            for index in range(len(sources)):
                if sources[index] == autoplay:
                    return index

        # if we need to let the user resolve manually, we need individual links as choices
        return select('Select source', sources)

    def __getNumberedSources(self):
        '''get a numbered version of the source list so that the user can select one (megavideo#1, megavideo#2, ...)
        @return: a map equivalent to the current available sources, but where the keys have numbers'''
        flattenedSources = {}
        for source, urls in self.sources.iteritems():
            for url in urls:
                flattenedSources["%s#%d" % (source, urls.index(url))] = [url]
        return flattenedSources


class Source(object):
    """represents a source of a certain media file that this module can translate into playable urls
    A source uses a link resolver to to the host specific tricks to ge the links.
    A media target (movie, tv show episode) may have multiple links on a host, so this source supports the
    concept of alternate urls and will try to resolve from one of them"""
    def __init__(self, urls, type):
        ''' initializes this source which involves deciding which resolver to use for this source host.
        If the type is not supported (has no LinkResolver for it) a LoopingLinkResolver will be used that will
        loop through all available link resolvers and try until one suceeds, as a fallback.
        @param urls: the urls on the host that should be translated into playable files
        @param type: the source type (this maps to the LinkResolver implementation to use)'''
        log.warning("type: %s" % str(type))
        if isSupported(type):
            self.__resolver = resolversMap[type]
            log.info("Selected resolver '%s' for type: %s" % (str(self.__resolver), str(type)))
        else:
            log.warning("No resolver found for type: %s" % str(type))
            self.__resolver = LoopingLinkResolver()
        self.__sourceName = type
        self.__urls = urls

    def __resolveAlternate(self, url):
        '''resolve one of the alternate links for a certain media target.
        will make the request to load the html page and pass it on to the LinkResolver to do the actual resolving
        @param url: the alternate target url to resolve
        @return: the resolved playable url
        @raise UnresolvableSourceException: if we found no links for this alternate url'''
        log.debug("Resolving alternative link %s" % (url))
        url = htmlutils.resolveRedirect(url)
        log.debug("Real link to resolve is %s" % (url))
        links = self.__resolver.resolve(url)
        if links:
            log.debug("Found part items: %s" % links)
            return links
        raise UnresolvableSourceException("No links found for '%s' on host '%s'" % (url, self.__sourceName))

    def resolve(self):
        """resolves one of the available alternate versions of a playable item
        @return: the resolved playable url for XBMC
        @raise UnresolvableSourceException: if none of the alternate links can be resolved"""
        for url in self.__urls:
            try:
                notifier = notification.getUserNotifier('Looking for playable link...', 'trying link %s of %s' % (self.__urls.index(url), len(self.__urls)))
                try:
                    return self.__resolveAlternate(url)
                except:
                    log.exception("Failed to resolve alternate link")
            finally:
                notifier.close()
        raise UnresolvableSourceException("No links found on %s" % (self.__sourceName))
