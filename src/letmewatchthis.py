# -*- coding: UTF-8 -*-
'''
This module implements the harvesting of links and metadata from 1channel.ch 

This implements a simple plugin flow:
  --> movies --> movie item --> play!
  --> tv shows --> tv show --> episode --> play!

Created on Dec 5, 2010

@author: pguedes
'''
import logging
from metadata.metadata import Metadata
from utils.pluginsupport import encode
from plugin import PluginMovieItem, PluginResult
import metadata.metadata as metadatautils
import utils.htmlutils as http
import xbmc #@UnresolvedImport
import urllib, re
from utils import settings
import plugin

log = logging.getLogger("letmewatchthis")

MODE_LIST_CATEGORY = 'category'
MODE_PLAY_ITEM = 'play'
MODE_LIST_EPISODES = 'episodes'
MODE_SEARCH = 'search'
MODE_RSS = 'rss'

SEARCH_SECTION_MOVIES = '1'
SEARCH_SECTION_TV = '2'
SEARCH_URL_TPL = 'http://www.1channel.ch/index.php?search_keywords=%s&search_section=%s'

CATEGORY_ITEM_PATTERN = '<div class="index_item index_item_ie"><a href="([^"]+?)" title="Watch ([^\(]+?) \((\d+)\)".+?img.+?src="([^"]+?)".+?</a>.+?</div></div>'
EPISODE_ITEM_PATTERN = '<div class="tv_episode_item">.+?href="(.+?)">.+?> - (.+?)</span>.+?</div>'
TVSHOW_METADATA_PATTERN = '<div class="movie_info">.+?<p.+?>(.+?):(.+?)</p>.+?<img.+?src="(.+?)".+?>.+?</div>'
SOURCE_PATTERN = '(/external.php.+?)".+?<span class="version_host">(.+?)</span>'

ALPHA_FILTER = "#"

plugin.normalFlowActions.append("selectSource")

@plugin.root()
def listCategories():
    '''List the root categories for this plugin
    @return: a list of PluginMovieItems with the root categories'''
    return PluginResult(7, [ LWTPluginMovieItem("Tv", 'http://www.1channel.ch/?tv=&sort=featured', MODE_LIST_CATEGORY),
                            LWTPluginMovieItem("Movies", 'http://www.1channel.ch/', MODE_LIST_CATEGORY),
                            LWTPluginMovieItem("Search Movies", '', MODE_SEARCH),
                            LWTPluginMovieItem("Search Tv Shows", '', MODE_SEARCH, extraArgs={'search_section': SEARCH_SECTION_TV})])

def categoryContentType(params):
    url = params['url']
    if url.find('?tv') >= 0:
        return 'tvshows'
    elif url.find('?music') >= 0:
        return 'artists'
    else:
        return 'movies'

def _listLetters(url, name):
    # one item for all non-alphabetical titles
    items = [LWTPluginMovieItem(ALPHA_FILTER, url, MODE_LIST_CATEGORY, extraArgs={"letter": ALPHA_FILTER})]
    # one item per letter in the alphabet
    from string import ascii_uppercase
    for letter in ascii_uppercase:
        items.append(LWTPluginMovieItem(letter, url, MODE_LIST_CATEGORY, extraArgs={"letter": letter}))
    return PluginResult(len(items), items)

@plugin.mode(MODE_LIST_CATEGORY, categoryContentType)
def listCategory(url, name, letter=None):
    log.debug("calling list categories %r" % name)
    if settings.isSet("group-categories-by-letter") and not letter:
        log.debug("listing all letter filters for category %r" % name)
        return _listLetters(url, name)
    # delegate to listCategoryLetter with no filter, to list all
    log.debug("listing with no letter filter for category %r" % name)
    return _listCategory(url, name, letter)

def _listCategory(url, name, letter=None):
    '''List all the TVShows/Movies/... available
    @param url: url of the title being refreshed
    @param label: the label of the title being refreshed (used for querying)
    @param letter: letter to filter on '#' for non-letter
    @return: a list of PluginMovieItemss'''
    def _shouldInclude(name):
        if not letter or letter == ALPHA_FILTER and not name[0].isalpha():
            return True
        return letter == name[0]

    log.debug("requesting url %r for category %r" % (url, name))
    page = http.get(url, cleanup=True)
    #log.debug(page)
    match = re.compile(CATEGORY_ITEM_PATTERN).findall(page)
    #log.debug("Results: %s"%str(match))
    if letter:
        match = [item for item in match if _shouldInclude(item[1])]
    size = len(match)
    def itemGenerator():
        for itemUrl, name, year, thumb in match:
            mode = _getMode(url)
            log.debug("creating item: title: '%s' URL: '%s' mode:'%s'" % (str(name), str(itemUrl), str(mode)))
            metadata = metadatautils.get(url, title=name, cover=thumb).year(int(year))
            log.debug("creating item: '%s'" % str(metadata))
            yield LWTPluginMovieItem(name, itemUrl, mode, metadata)
        nextpageurl = __getNextPageUrl(url)
        log.debug("next page: '%s'" % str(nextpageurl))
        yield LWTPluginMovieItem("more...", nextpageurl, MODE_LIST_CATEGORY)

    log.debug("found result of size %r" % name)
    return PluginResult(size, itemGenerator)

def __url(url):
    return "http://www.1channel.ch" + url

def __getNextPageUrl(url):
    pageregex = re.compile("=&page=(.+)")
    currentpage = pageregex.findall(url)
    if len(currentpage) > 0:
        currentpagenum = int(currentpage[0])
        return pageregex.sub("=&page=%d" % (currentpagenum + 1), url)
    if url.find("?tv") > 0:
        return __url("/index.php?tv=&page=2")
    return __url("/index.php?page=2")

def __parseTvShowMetadata(html):
    tvshowmeta = re.compile(TVSHOW_METADATA_PATTERN, re.DOTALL).findall(html)[0]
    return Metadata(tvshowmeta[0].strip(), tvshowmeta[1].strip(), tvshowmeta[2].strip())

@plugin.mode(MODE_LIST_EPISODES, contentType='episodes')
def listEpisodes(url, name):
    '''List the episodes for a TV Show
    @param url: the tvshack url to load episodes from
    @param label: the tvshow being listed
    @return: a list of LWTPluginMovieItem with the episode items'''
    url = __url(url)
    html = http.get(url, cleanup=True)

    tvshowmeta = __parseTvShowMetadata(html)

    episodeLinks = re.compile(EPISODE_ITEM_PATTERN, re.DOTALL).findall(html)
    itemCount = len(episodeLinks)
    def itemGen():
        episodeurl = None
        for episodeurl, episodetitle in episodeLinks:
            episodeMetadata = tvshowmeta.title(episodetitle)
            log.debug("creating item: '%s'" % str(episodeMetadata))
            yield LWTPluginMovieItem(episodetitle, episodeurl, MODE_PLAY_ITEM, episodeMetadata)

    return PluginResult(itemCount, itemGen)


def getSourceName(sourceClob):
    name = re.compile("document.writeln\(\'(.+?)\'\)", re.DOTALL).findall(sourceClob)
    if name:
        return name[0]

    if sourceClob.find('host_48.gif'):
        return 'putlocker'
    if sourceClob.find('host_45.gif'):
        return 'sockshare'

@plugin.mode(MODE_PLAY_ITEM, playable=True)
def resolveFiles(url, name, forceSourceSelection=False):
    '''Resolve the files for a movie/episode/... item
    
    Resolving a file is split into three phases:
    1-Select file source (megavideo, veoh, tudou, youku, ...)
    2-Load parts (if item is split for the selected source)
    3-Resolve file links for the parts from the previous step
    
    If an item has only one available source, then that source is auto-selected, otherwise
    the user is shown a XBMC dialog to select the source. If the 'autoplay-preferred-source'
    setting is enabled, the first available source that matches the 'preferred-source' setting
    will be auto-selected.
    
    @param url: the url to resolve files for
    @param label: the label of the playable item being resolved
    @param forceSourceSelection: if the user should be forced to select the source (default False)
    @return: a list of urls of the files to play'''
    log.debug("Listing sources: %s, forceSelection: %s" % (url, forceSourceSelection))
    html = http.get(__url(url), cleanup=True)

    alternateLinks = [(itemUrl, getSourceName(itemSource)) for (itemUrl, itemSource) in re.compile(SOURCE_PATTERN, re.DOTALL).findall(html)]
    log.debug("found links in page: %s" % str(alternateLinks))
    from linkresolvers import SourceList
    sources = SourceList([(__url(url), name) for url, name in alternateLinks],
                         settings.isSet("filter-unsupported-sources"))

    autoSelectSource = None
    if settings.isSet("autoplay-preferred-source"):
        autoSelectSource = settings.get("preferred-source")

    selected = sources.selectSource(forceSourceSelection, autoSelectSource)
    if selected:
        metadata = __parseTvShowMetadata(html)
        link = selected.resolve()
        log.debug("resolved link for video: %s" % str(link))
        return PluginResult(1, [LWTPluginMovieItem(name, link, metadata=metadata)])
#    return PluginResult(-1, [LWTPluginMovieItem(name, link, metadata=metadata) for link in links])

@plugin.mode(MODE_SEARCH)
def search(search_section=SEARCH_SECTION_MOVIES):
    '''Do an interactive search of tvshack.cc's files
    @return: list of files matching search criteria'''
    keyb = xbmc.Keyboard('', 'Search 1channel.ch')
    keyb.doModal()
    if (keyb.isConfirmed()):
        search = keyb.getText()
        encode = urllib.quote(search).replace(' ', '+')
        html = http.get(SEARCH_URL_TPL % (encode, str(search_section)), cleanup=True)
        match = re.compile(CATEGORY_ITEM_PATTERN).findall(html)
        def itemGen():
            for itemUrl, name, year, thumb in match:
                log.debug("found item: title: '%s' URL: '%s'" % (str(name), str(itemUrl)))
                metadata = metadatautils.Metadata(name, cover=thumb).year(int(year))
                resultsmode = MODE_PLAY_ITEM
                if search_section == SEARCH_SECTION_TV:
                    resultsmode = MODE_LIST_EPISODES
                yield LWTPluginMovieItem(name, itemUrl, resultsmode, metadata)
        return PluginResult(len(match), itemGen)
    return PluginResult(0, [])

class LWTPluginMovieItem(PluginMovieItem):
    """PluginMovieItem for 1channel.ch"""
    def __init__(self, name, url, mode=None, metadata=None, tags="", extraArgs=None):
        """Create an item 
        @param label: the label for this item
        @param url: the url to load this item
        @param metadata: the metadata to show this item in XBMC
        @param tags: the tags to show """
        PluginMovieItem.__init__(self, name, url, mode, extraArgs)
        self.metadata = metadata
        self.title = name + tags

    def getTitle(self):
        return self.title

    def getLabels(self):
        if self.metadata:
            return self.metadata.getLabels()
        return PluginMovieItem.getLabels(self)

    def hasFanart(self):
        return self.hasMetadata() and self.metadata.hasFanart() and settings.isSet("load-tv-fanart")

    def hasMetadata(self):
        return self.metadata is not None

    def hasCover(self):
        return self.hasMetadata() and self.metadata.getCover() is not None

    def getCover(self):
        return self.metadata.getCover();

    def getFanart(self):
        return self.metadata.getFanart();

    def buildContextMenu(self):
        """ Builds the context menu for the xbmc-tvshack plugin
        @param pluginItem: the plugin item to create a context menu for"""
        contextMenu = [("Reload listing", "Container.Refresh")]
        if self.isPlayable():
            contextMenu.append(("Select source", "XBMC.PlayMedia(%s)" % self.getTargetUrl('selectSource',
                                                                        extra={"forceSourceSelection": "1"})))
        return contextMenu

def _getMode(url):
    '''Get the execution mode for this plugin
    The execution mode is used by the plugin to track the type of url being used
    @param url: the url to get the execution mode for'''
    mode = MODE_PLAY_ITEM
    if url.find('?tv') >= 0:
        mode = MODE_LIST_EPISODES
    return mode
