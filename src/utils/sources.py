# -*- coding: UTF-8 -*-
"""A module about transforming a playable item selection into urls that can be played by XBMC's player.

This module contains three main abstractions:
 - source: a website that hosts the actual media we want to play (@see: Source)
 - source list selection: how do we select the source to play (preferred source, manual selection) (@see: SourceList)
 - link resolvers: implementation of specific strategies to grab the actual media links from the sources (@see: LinkResolver)

The Source class provides an interface for this module.
A source is one of the media hosting websites which is directly tied to a link resolver.
By instantiating a Source, you get an object with a 'resolve' method that will call the linkresolver for that website and return
the collected links or raise an exception if it cannot.

The SourceList class implements the logic of selecting a Source out of a set of currently available ones.

Actually resolving the links is handled by a separate module by ElDorado (script.module.urlresolver)

@author: pguedes
"""
from utils.pluginsupport import select
import logging
from utils import notification

log = logging.getLogger("linkresolvers")


class UnresolvableSourceException(Exception):
    """exception raised when a source's links cannot be resolved"""
    pass


class NoSourceSelectedException(Exception):
    """exception raised when a source cannot be selected"""
    pass


class LinkResolver(object):
    """interface for link resolver objects
    NOTE: python does not have interfaces and most of the code is old and does not implement this. for documentation
    purposes"""
    def resolve(self, url):
        """resolve the links on the page
        @param url: the url of the page to get links for
        @return: the list of resolved playable urls for XBMC's player"""


class SourceList(object):
    """This class encapsulates the logic of selection of a source from a list of available one.
    Each media target (a movie, or an episode of a show), is typically hosted on multiple source sites (hosters)
    @see: selectSource"""
    def __init__(self, links, filterUnsupportedSources=False):
        """create a new SourceList to select from a list of sources.
        @param links: a list of tuples with (url, name) of sources to use as choices for source selection"""
        self.sources = {}
        for url, source in links:
            self.sources.setdefault(source, []).append(url)

    def selectSource(self, forceSourceSelection=False, autoplay=None):
        """selects one out of the available sources.
        If a selection is envolved will either autoselect the autoplay source or allow the user to choose.
        @param forceSourceSelection: if true the user will allways have to choose the source manually
        @param autoplay: the preferred source to auto-select if choosing is involved
        @return: the selected Source
        @raise NoSourceSelectedException: raised when no source was selected"""
        log.debug("Selecting from sources: %r" % self.sources)

        sources = self.sources
        if forceSourceSelection:
            sources = self.__getNumberedSources()

        sourceNames = sources.keys()

        selected = self._selectSource(sourceNames, forceSourceSelection, autoplay)
        if selected >= 0:
            selectedSourceType = sourceNames[selected]
            return Source(sources[selectedSourceType], selectedSourceType)

        raise NoSourceSelectedException('no source selected to play')

    def _selectSource(self, sources, forceSourceSelection, autoplay=None):
        """select one source out of a list of possible.
        Automatically selects:
         - if there is only one source, that one
         - if there is an option and one of the options is the autoplay one, then that
        Otherwise delegates selection to the user via the pluginsupport.select() method.
        @param sources: the list of possible sources
        @param forceSourceSelection: if true and there is an option it will be left for the user
        @param autoplay: the preferred selection to auto-select if there is an option and we do not want to force the
            user to select
        @return: the selected source (@see: Source)"""
        if not sources:
            return - 1
        elif len(sources) == 1:
            return 0
        elif autoplay and not forceSourceSelection:
            for index in range(len(sources)):
                if sources[index] in autoplay:
                    return index

        # if we need to let the user resolve manually, we need individual links as choices
        return select('Select source', sources)

    def __getNumberedSources(self):
        """get a numbered version of the source list so that the user can select one (megavideo#1, megavideo#2, ...)
        @return: a map equivalent to the current available sources, but where the keys have numbers"""
        flattenedSources = {}
        for source, urls in self.sources.iteritems():
            for url in urls:
                flattenedSources["%s#%d" % (source, urls.index(url))] = [url]
        return flattenedSources


class Source(object):
    """represents  source of a certain media file that this module can translate into playable urls
    A source uses a link resolver to to the host specific tricks to ge the links.
    A media target (movie, tv show episode) may have multiple links on a host, so this source supports the
    concept of alternate urls and will try to resolve from one of them"""

    def __init__(self, urls, type):
        """ initializes this source which involves deciding which resolver to use for this source host.
        If the type is not supported (has no LinkResolver for it) a LoopingLinkResolver will be used that will
        loop through all available link resolvers and try until one succeeds, as a fallback.
        @param urls: the urls on the host that should be translated into playable files
        @param type: the source type (this maps to the LinkResolver implementation to use)"""
        log.warning("type: %s" % str(type))
        self.__sourceName = type
        self.__urls = urls

    def __resolveAlternate(self, url):
        """resolve one of the alternate links for a certain media target.
        will make the request to load the html page and pass it on to the LinkResolver to do the actual resolving
        @param url: the alternate target url to resolve
        @return: the resolved playable url
        @raise UnresolvableSourceException: if we found no links for this alternate url"""

        from urlresolver import HostedMediaFile

        log.debug("Resolving alternative link %s" % (url))
        links = HostedMediaFile(url).resolve()
        log.debug("resolved:  %s" % links)
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
                notifier = notification.getUserNotifier('Looking for playable link...', 'trying link %s of %s' % (
                self.__urls.index(url), len(self.__urls)))
                try:
                    return self.__resolveAlternate(url)
                except:
                    log.exception("Failed to resolve alternate link")
            finally:
                notifier.close()
        raise UnresolvableSourceException("No links found on %s" % self.__sourceName)
