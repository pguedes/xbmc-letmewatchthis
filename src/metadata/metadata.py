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
import logging
from utils.notification import getUserNotifier
from os.path import getsize, exists
from unicodedata import normalize
from searchers import imdb, tvdb
from searchers.adapters import MetadataProvider
from utils import settings

import pickle, re, os, sys
import xbmc, xbmcgui #@UnresolvedImport

METADATA_PATH_ROOT = xbmc.translatePath(sys.argv[0])
METADATA_PATH_FORMAT = "%s.metadata"
TVSHOW_TYPE, MOVIES_TYPE, ANIME_TYPE = "tvseries", "movies", "anime"

log = logging.getLogger('metadata')
metadataLoader = MetadataProvider()

def _getMetadataPath(type):
  '''
  Get the path to the metadata file of a type
  @param type: the type of metadata file to load (tvseries, movies, or a tv show title for it's episodes file)
  @return: file system path to the metadata cache file
  '''
  return os.path.join(_getMetadataRoot(), METADATA_PATH_FORMAT % type)
 
def _getMetadataRoot():
  '''
  Get the path to the root of the metadata files
  @return: file system path to the root of the cache files (<plugin root>/cache/)
  '''
  return os.path.join(os.getcwd(), "cache")
 
def _readDictionary(file):
  '''
  Unpickle a dictionary from the file system
  @param file: the file system path to load the file from
  @return: the loaded dictionary
  '''
  if exists(file) and getsize(file) > 0:
    log.debug("Loading dictionary from file '%s'" % file)
    f = open(file)
    try:
      return pickle.load(f)
    finally:
      f.close()

def _saveDictionary(file, dict):
  f = open(file, "w")
  try:
    try:
      log.debug("writing dictionary %s to file '%s'" % (dict, f))
      pickle.dump(dict, f)
    except:
      log.exception("failed to write dictionary %s to file '%s'" % (dict, f))
  finally:
    f.close()

class MetadataCache:
  
  class __impl:
    
    def __init__(self, entry):
      self.__file = entry.getCachePath()
      log.info("Loading metadata cache from file system: %s" % self.__file)
      self.__cache = _readDictionary(self.__file)
      if not self.__cache:
        self.__cache = {}
      log.debug("initted metadata cache")
      
    def save(self):
      '''
      Persist the cache to the file system.
      Will create the metadata root directory if it doesn't exist.
      '''
      metaroot = _getMetadataRoot()
      if not os.path.isdir(metaroot):
        log.info("Creating initial cache dir: %s" % metaroot)
        os.makedirs(metaroot)
      f = open(self.__file, "w")
      try:
        log.debug("saving metadata cache=%s to file '%s'" % (self.__cache, f))
        pickle.dump(self.__cache, f)
      finally:
        f.close()
  
    def contains(self, entry, lookupEpisodes=True):
      '''
      Test if an item is in cache
      For tv shows, returns true if a .tvmetadata-<TVSHOW>.cache file exists
      @param entry: the MetadataKey to check for 
      '''
      contained = self.__cache.has_key(entry.getKey())
      if not contained and entry.isTVShow() and lookupEpisodes:
        episodesFile = entry.getEpisodeCachePath()
        log.debug("Looking for cached episodes for '%s' file: %s" % (entry.getKey(), episodesFile))
        contained = exists(episodesFile) and getsize(episodesFile) > 0
      log.debug("Checking cache for '%s' returning %s" % (entry.getKey(), str(contained)))
      return contained
  
    def lookup(self, entry):
      '''
      Lookup an entry in cache
      @param entry: MetadataKey to lookup
      @return: the Metadata entry in cache or None if not found
      '''
      log.debug("looking up cached metadata for entry '%s'" % entry.getKey())
      if self.__cache.has_key(entry.getKey()):
        return self.__cache[entry.getKey()]
      if entry.isTVShow():
        episodesFile = entry.getEpisodeCachePath()
        if exists(episodesFile) and getsize(episodesFile) > 0:
          log.debug("Loading cached tv show '%s' data in episodes file: %s" % (entry.getKey(), episodesFile))
          entries = _readDictionary(episodesFile)
          if entries.has_key(entry.getKey()):
            return entries[entry.getKey()]
      log.debug("entry '%s' not found in cache" % entry.getKey())
      return None
    
    def refresh(self, url, metadata, persist=False):
      '''
      Refresh an entry with new metadata. Optionally persist to file system.
      @param url: the url of the entry to update
      @param metadata: the metadata to update with
      @param persist: if the update should be persisted to the file system (default False)
      '''
      log.debug("Refreshing metadata for url '%s': %s" % (url, metadata))
      copy = Metadata().copy(metadata)
      self.__cache[url] = copy
      if persist:
        self.save()
      
  __instance = None # singleton instance of the cache
      
  def __init__(self, type):
    '''
    Return a singleton instance (unpickle once)
    '''
    if MetadataCache.__instance is None:
      MetadataCache.__instance = MetadataCache.__impl(type)

    self.__dict__['_MetadataCache__instance'] = MetadataCache.__instance

  def __getattr__(self, name):
    return getattr(self.__instance, name)

  def __setattr__(self, name, value):
    return setattr(self.__instance, name, value)


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

class MetadataKey:
  useTvShowCache = False
  '''
  A key to the metadata database, translates urls
  '''
  def __init__(self, url, title=None):
    '''
    Build a new key
    @param url: the url to map
    @param title: the title to use for searching, if needed
    '''
    if url.find('http://') < 0:
      url = "http://tvshack.cc" + url
    if title is not None and title.find('(') > 0:
      title = re.sub("\(.+?\)", "", title)  
    self.__title = title;
    self.__url = url
    self.__key = re.compile("http://tvshack.cc/(.+?/.+?)/").findall(self.__url)[0]
    
    if self.__key.startswith("tv"):
      self.__type = TVSHOW_TYPE
    elif self.__key.startswith("anime"):
      self.__type = ANIME_TYPE
    else:
      self.__type = MOVIES_TYPE
      
    if self.isEpisode():
      season, episode = self.getSeasonAndEpisode()
      self.__key = self.getEpisodeKey(season, episode)

  def getEpisodeKey(self, season, episode):
    '''
    Get the episode key into the metadata
    @param season: the season for the key
    @param episode: the episode for the key
    @return: the episode key (e.g: tv/Dexter/S2E5)
    '''
    return "%s/S%sE%s" % (self.__key, season, episode)
  
  def getEpisodeCachePath(self):
    '''
    Get the path to the episodes metadata cache
    @attention: only applies to tvshow items, otherwise use getCachePath
    @return: full file system path to the episodes cache file
    '''
    if self.isTVShow():
      return _getMetadataPath(self.__key.replace('/', '-'))
  
  def setUseTVShowCache(self, active=True):
    self.useTvShowCache = active
    return self
  
  def getCachePath(self):
    '''
    Get the path to the metadata cached database on the file system.
    This will be video.metadata or tv.metadata or tv/_Till_Death.metadata
    @return: full file system path to the cache file for this entry
    '''
    if self.useTvShowCache:
      return self.getEpisodeCachePath()
    file = '-'.join(self.__key.split('/')[:-1])
    return _getMetadataPath(file)
  
  def getParentKey(self):
    '''
    For episodes returns the MetadataKey for the tvshow, else None
    '''
    if self.isEpisode():
      parentUrl = re.compile("(http://tvshack.cc/.+?/.+?/)").findall(self.__url)[0]
      return MetadataKey(parentUrl)

  def getKey(self):
    '''
    Get the key string
    '''
    return self.__key
   
  def getSeasonAndEpisode(self):
    '''
    Attempt to grab the season and episode from the tvshack.cc url
    '''
    return re.compile("http://tvshack.cc/.+?/.+?/season_(.+?)/episode_(.+?)/").findall(self.__url)[0]
  
  def isEpisode(self):
    '''
    Check if this key is for an tv show episode
    @return: True if this is of type tvshow and the url of depth > 4
    '''
    return self.__type == TVSHOW_TYPE and len(self.__url.split('/')) > 6

  def isMovie(self):
    '''Check if this key is of type movies
    @return: True if this is of type movies'''
    return self.__type == MOVIES_TYPE
  
  def isAnime(self):
    '''Check if this key is of type anime
    @return: True if this is of type anime'''
    return self.__type == ANIME_TYPE
  
  def isTVShow(self):
    '''
    Check if this key is of type tvshow
    @return: True if this is of type tvshow and the url of depth <= 4
    '''
    return self.__type == TVSHOW_TYPE and len(self.__url.split('/')) <= 6

  def getName(self):
    '''
    Get the cleaned name from this key
    @return: the second part of the key after removing numbers and _ 
    '''
    if self.__title:
      return self.__title
    name = self.__key.split('/')[1]
    name = re.sub("__[0-9]+?_", " ", name).replace('_', ' ')
    if name.find('(') > 0:
      name = re.sub("\(.+?\)", "", name)
    return name
  
  def getType(self):
    '''
    Get the type for this key (tvshow, movies or episodes)
    '''
    return self.__type
  
  def __str__(self):
    return "key='%s'; url='%s'; name='%s', type=%s" % (self.__key, self.__url, self.getName(), self.__type)

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
  @return: metadata for the url
  '''
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
