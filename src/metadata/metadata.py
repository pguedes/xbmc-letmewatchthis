# -*- coding: UTF-8 -*-
'''
Created on Jan 17, 2010

List of metadata supported by XBMC for video files:
    genre       : string (Comedy)
    year        : integer (2009)
    episode     : integer (4)
    season      : integer (1)
x    top250      : integer (192)
x    tracknumber : integer (3)
    rating      : float (6.4) - range is 0..10
x    playcount   : integer (2) - number of times this item has been played
x    overlay     : integer (2) - range is 0..8.  See GUIListItem.h for values
    cast        : list (Michal C. Hall)
    castandrole : list (Michael C. Hall|Dexter)
    director    : string (Dagur Kari)
x    mpaa        : string (PG-13)
    plot        : string (Long Description)
    plotoutline : string (Short Description)
    title       : string (Big Fan)
    duration    : string (3:18)
    studio      : string (Warner Bros.)
x    tagline     : string (An awesome movie) - short description of movie
    writer      : string (Robert D. Siegel)
    tvshowtitle : string (Heroes)
    premiered   : string (2005-03-04)
x    status      : string (Continuing) - status of a TVshow
    code        : string (tt0110293) - IMDb code
x    aired       : string (2008-12-07)
x    credits     : string (Andy Kaufman) - writing credits
x    lastplayed  : string (%Y-%m-%d %h:%m:%s = 2009-04-05 23:16:04)
x    album       : string (The Joshua Tree)
    votes       : string (12345 votes)
x    trailer     : string (/home/user/trailer.avi)

@author: pguedes
'''
import logging, re
from unicodedata import normalize
from searchers.adapters import MetadataProvider
from utils import settings
from localcache import MetadataCache, MetadataKey

TVSHOW_TYPE, MOVIES_TYPE, ANIME_TYPE = "tvseries", "movies", "anime"

log = logging.getLogger('metadata')
metadataLoader = MetadataProvider()

class Metadata:
  '''
  Collection/builder of info labels for XBMC.
  '''
  def __init__(self, title="", plot="", cover=""):
    '''
    Create a new metadata instance
    @param title: title for the item
    @param plot: plot for the item
    @param cover: cover for the item
    '''
    self.__infoLabels = {}
    if len(title) > 0:
      self.title(title)
    if len(cover) > 0:
      self.cover(cover)
    if len(plot) > 0:
      self.plot(plot)

  def __setitem__(self, key, value):
    if not self.__infoLabels:
      self.__infoLabels = {}
    self.__infoLabels[key] = value

  def __set(self, label, value):
    '''
    Set infolabel value and return self to be usable as a builder
    @param label: info label to set
    @param value: value for the label
    @return: this Metadata instance
    '''
    self.__infoLabels[label] = value
    return self

  def __setUnicode(self, label, value, cleanup=False):
    '''
    Unicode safe set for an info label value
    @param label: the info label to set
    @param value: the text value to convert to unicode before setting
    @return: this Metadata instance
    '''
    unicode_value = value
    if not isinstance(value, unicode):
      #log.debug("fixing to unicode %s"%value)
      unicode_value = _smart_unicode(value)
      log.debug("fixed to unicode %s" % unicode_value)
    if cleanup:
      unicode_value = unicode_value.replace('&eacute;', 'ea')
      unicode_value = unicode_value.replace('&amp;', '&')
      unicode_value = unicode_value.replace('&quot;', '')
      unicode_value = unicode_value.replace('&#x22;', '')
      unicode_value = unicode_value.replace('\n', ' ')
      unicode_value = unicode_value.replace('\r', ' ')
      unicode_value = unicode_value.replace('&quot;', '"')

    if unicode_value:
      unicode_value = normalize("NFKD", unicode_value).encode('UTF-8', 'ignore')
    log.debug("Fixed String: %s" % str(unicode_value))
    return self.__set(label, unicode_value)

  def copy(self, other):
    '''
    Copy another Metadata instance's info labels
    @param other: Metadata instance to copy labels from
    '''
    self.__infoLabels = other.getLabels().copy()
    return self

  def code(self, code):
    '''
    Set the code for this metadata
    @param code: the id for this metadata's system
    @return: this Metadata instance
    '''
    return self.__set("code", code)

  def getId(self):
    '''
    Get the code for this metadata
    @return: this Metadata's code (info label)
    '''
    if not self.__infoLabels.has_key("code"):
      return None
    return self.__infoLabels["code"]

  def genre(self, genre):
    '''
    Set the genre for this metadata
    @param genre: "genre" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("genre", genre)

  def year(self, year):
    '''
    Set the year for this metadata
    @param year: "year" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("year", year)

  def cover(self, cover):
    '''
    Set the cover for this metadata
    @param cover: "cover" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("cover", cover)

  def studio(self, studio):
    '''
    Set the studio for this metadata
    @param studio: "studio" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("studio", studio)

  def rating(self, rating):
    '''
    Set the rating for this metadata
    @param rating: "rating" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("rating", rating)

  def votes(self, votes):
    '''
    Set the votes for this metadata
    @param votes: "votes" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("votes", votes)

  def plotoutline(self, plot):
    '''
    Set the plot for this metadata
    @param plot: "plotoutline" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("plotoutline", plot, True)

  def plot(self, plot):
    '''
    Set the plot for this metadata
    @param plot: "plot" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("plot", plot, True)

  def director(self, director):
    '''
    Set the director for this metadata
    @param director: "director" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("director", director)

  def writer(self, writer):
    '''
    Set the writer for this metadata
    @param writer: "writer" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("writer", writer)

  def duration(self, duration):
    '''
    Set the duration for this metadata
    @param duration: "duration" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("duration", duration)

  def cast(self, cast):
    '''
    Set the cast for this metadata
    @param cast: "cast" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("cast", cast)

  def castandrole(self, cast):
    '''
    Set the cast (with roles) for this metadata
    @param cast: "castandrole" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("castandrole", cast)

  def title(self, title):
    '''
    Set the title for this metadata
    @param title: "title" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("title", title)

  def tvshow(self, show):
    '''
    Set the tvshow title for this metadata
    @param show: "tvshowtitle" info label value to set
    @return: this Metadata instance
    '''
    return self.__setUnicode("tvshowtitle", show)

  def tvshowid(self, show):
    '''
    Set the tvshow id for this metadata
    @param show: "tvshowid" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("tvshowid", show)

  def premiered(self, premiered):
    '''
    Set the premiered for this metadata
    @param premiered: "premiered" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("premiered", premiered)

  def episode(self, episode):
    '''
    Set the episode for this metadata
    @param episode: "episode" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("episode", episode)

  def getTitle(self): return self.__infoLabels["title"]
  def getSeason(self): return self.__infoLabels["season"]
  def getEpisode(self): return self.__infoLabels["episode"]
  def getTvShowId(self): return self.__infoLabels["tvshowid"]

  def getSeasonedTitle(self, pattern="S%sE%s - %s"):
    '''
    Return a the title for this item
    @param pattern: the string pattern for the title (default "S%sE%s - %s")
    @return: the pattern passed in season episode and title (pattern % (season, episode, title)) 
    '''
    return pattern % (self.__infoLabels["season"], self.__infoLabels["episode"], self.__infoLabels["title"])

  def hasFanart(self):
    '''
    Check if the fanart label has been set
    '''
    return self.__infoLabels.has_key("fanart")

  def getFanart(self):
    '''
    Get the fanart value for this metadata
    '''
    return self.__infoLabels['fanart']

  def fanart(self, fanart):
    '''
    Set the fanart link for this metadata
    @param fanart: "fanart" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("fanart", fanart)

  def season(self, season):
    '''
    Set the season for this metadata
    @param season: "season" info label value to set
    @return: this Metadata instance
    '''
    return self.__set("season", season)

  def getCover(self):
    '''
    Get the cover.
    If the cover link is from IMDB, we resize it through it's url
    @return: a cover url, or an emtpy string
    '''
    cover = self.__infoLabels["cover"] or ""
    if not cover.startswith("http://"):
      return ""
    try:
      if re.compile("http://ia\.media-imdb\.com/images/.+?_SX\d+?_SY\d+?_\.jpg").match(cover):
        coversize = settings.get("imdb-cover-size")
        cover = re.sub('_SX\d+_SY\d+_\.jpg', "_SX%s_.jpg" % str(coversize), cover)
    except:
      log.exception("Could not resize cover: '%s'" % cover)
    return cover

  def getLabels(self):
    '''
    Return the collected info labels in this metadata
    '''
    return self.__infoLabels

  def hasCode(self):
    '''
    Check if this metadata is linked to an online metadata db
    '''
    return self.__infoLabels.has_key("code")

  def isEmpty(self):
    '''
    Check if this metadata contains any valuable data
    @return: True if there is at least one label other than title with a value
    '''
    for k, v in self.__infoLabels.items():
      if v != "" and k != "title":
        return False
    return True

  def __str__(self):
    return "Metadata: %s" % str(self.__infoLabels)


def _smart_unicode(s):
  '''
  Encode a string in unicode
  @param s: string to encode
  @return: unicode encoded version of the string
  '''
  def _unicode_encode(encoding):
    if not isinstance(s, basestring):
      if hasattr(s, '__unicode__'):
        return unicode(s)
      else:
        return unicode(str(s), encoding)
    elif not isinstance(s, unicode):
      return unicode(s, encoding)

  if not s:
    return u''
  try:
    s = _unicode_encode('UTF-8')
  except:
    s = _unicode_encode('ISO-8859-1')
  return s

def flushCache(url):
    MetadataCache(MetadataKey(url)).save()

def get(url, plot="", cover="", queryOnlineDb=False, bypassCache=False, title=None, tvshow=None, persistUpdates=True):
    '''Get the metadata for an url.
    If possible, get the cached metadata, otherwise, query IMDB/THETVDB for it
    If this fails, return default metadata built with what is available from tv shack
    
    Will try to return from cache and if not possible will refresh cache with freshly built metadata
    
    A metadata key is in the format: <type>/<title> e.g: tv/How_I_met_your_mother
    
    @param url: the url to load metadata for
    @param plot: fallback plot to build default metadata with (default "")
    @param cover: fallback cover to build default metadata with (default "")
    @param queryOnlineDb: if we should search for items not in cache (default False)
    @param bypassCache: if we should bypass cache (to force searching) (default False)
    @param title: fallback title to build default metadata with (default None)
    @param tvshow: title of the tvshow (default None)
    @return: metadata for the url'''
    entry = MetadataKey(url, title)
    if entry.isTVShow() and tvshow:
        entry.setUseTVShowCache()

    log.debug("Created key for url: %s, %s" % (url, str(entry)))
    cache = MetadataCache(entry)
    log.debug("Cache loaded: %s" % id(cache))
    log.debug("Querying cache for entry: %s" % entry)
    cached = cache.lookup(entry)
    # only override cache if query is not disabled
    bypassCache = bypassCache and not settings.isSet("metadata-query-skip")
    if not bypassCache and cached is not None:
        if not cache.contains(entry, False):
            log.debug("Updating show cache from episodes cache...%s" % str(entry.getKey()))
            cache.refresh(entry.getKey(), cached, persist=True)
        #log.debug("Returning from cache...%s" % str(cached))      
        return cached

    log.debug("Not returning from cache... building new...")
    # build default metadata
    metadata = Metadata(entry.getName(), plot, cover)
    # coz episodes need more info to load metadata
    if entry.isEpisode():
        seasonNumber, episodeNumber = entry.getSeasonAndEpisode()
        metadata.season(seasonNumber).episode(episodeNumber)
        if tvshow:
            metadata.tvshow(tvshow.getTitle()).tvshowid(tvshow.getId()).cover(tvshow.getCover())
        elif cached:
            tvshowid = cached.getTvShowId()
            tvshowcover = cached.getCover()
            if not tvshowid or not tvshowcover:
                # look for the parent entry and try to load it from there
                tvshowentry = entry.getParentKey()
                tvshowmeta = cache.lookup(tvshowentry)
                tvshowid = tvshowmeta.getId() or tvshowid
                tvshowcover = tvshowmeta.getCover()
            log.info("Decorating with cached data, tvshowid = %s" % str(tvshowid))
            metadata.tvshowid(tvshowid).cover(tvshowcover)

    if queryOnlineDb and not settings.isSet("metadata-query-skip"):
        try:
            if entry.isMovie() or entry.isTVShow():
                dbid = metadataLoader.search(entry)
                if dbid:
                    log.info("Loading metadata for '%s'" % dbid)
                    metadataLoader.load(entry, metadata.code(dbid))
            elif entry.isEpisode():
                metadataLoader.load(entry, metadata)
        except:
            log.exception("Querying metadata failed")

    # update the cache
    if not metadata.isEmpty():
        cache.refresh(entry.getKey(), metadata, persistUpdates)
    return metadata
