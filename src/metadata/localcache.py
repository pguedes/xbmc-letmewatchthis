'''
Created on Nov 27, 2011

@author: pguedes
'''
import logging
from os.path import getsize, exists

import pickle, re, os, sys
import xbmc #@UnresolvedImport
import metadata as metadatautils

METADATA_PATH_ROOT = xbmc.translatePath(sys.argv[0])
METADATA_PATH_FORMAT = "%s.metadata"

log = logging.getLogger('metadata.localcache')


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
            '''Persist the cache to the file system.
            Will create the metadata root directory if it doesn't exist.'''
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
            '''Test if an item is in cache
            For tv shows, returns true if a .tvmetadata-<TVSHOW>.cache file exists
            @param entry: the MetadataKey to check for '''
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
            '''Refresh an entry with new metadata. Optionally persist to file system.
            @param url: the url of the entry to update
            @param metadata: the metadata to update with
            @param persist: if the update should be persisted to the file system (default False)'''
            log.debug("Refreshing metadata for url '%s': %s" % (url, metadata))
            copy = metadatautils.Metadata().copy(metadata)
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
      url = "http://1channel.ch" + url
    if title is not None and title.find('(') > 0:
      title = re.sub("\(.+?\)", "", title)
    self.__title = title;
    self.__url = url
    self.__key = url
    #self.__key = re.compile("http://.+?1channel.ch/(.+?/.+?)/").findall(self.__url)[0]

    if self.__key.startswith("tv"):
      self.__type = metadatautils.TVSHOW_TYPE
    elif self.__key.startswith("anime"):
      self.__type = metadatautils.ANIME_TYPE
    else:
      self.__type = metadatautils.MOVIES_TYPE

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
    return self.__type == metadatautils.TVSHOW_TYPE and len(self.__url.split('/')) > 6

  def isMovie(self):
    '''Check if this key is of type movies
    @return: True if this is of type movies'''
    return self.__type == metadatautils.MOVIES_TYPE

  def isAnime(self):
    '''Check if this key is of type anime
    @return: True if this is of type anime'''
    return self.__type == metadatautils.ANIME_TYPE

  def isTVShow(self):
    '''
    Check if this key is of type tvshow
    @return: True if this is of type tvshow and the url of depth <= 4
    '''
    return self.__type == metadatautils.TVSHOW_TYPE and len(self.__url.split('/')) <= 6

  def getName(self):
    '''
    Get the cleaned label from this key
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
    return "key='%s'; url='%s'; label='%s', type=%s" % (self.__key, self.__url, self.getName(), self.__type)

