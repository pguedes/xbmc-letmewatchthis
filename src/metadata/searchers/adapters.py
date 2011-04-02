# -*- coding: UTF-8 -*-
'''
Created on May 29, 2010

@author: pedro
'''
import tmdb, tvdb, logging
import xbmcgui #@UnresolvedImport
from utils import settings

log = logging.getLogger("tmdb")

class MetadataLoader(object):
  def choose(self, options, message):
    hits = len(options)
    if hits == 1:
      return options[0]['id']
    elif hits > 1:
      hitNames = [hit['name'] for hit in options]
      dialog = xbmcgui.Dialog()
      selected = dialog.select(message, hitNames)
      if selected >= 0:
        return options[selected]['id']
    
class TvDbMetadataLoader(MetadataLoader):
  def searchTvShow(self, title):
    log.info("Searching TVDB for '%s'" % title)
    series = tvdb.get_series(title)
    log.debug("Found series '%s'" % str(series))
    return self.choose(series, "Select Tv show...")

  def loadTvShow(self, metadata):
    log.debug("Loading details for tv show id: %s" % str(metadata.getId()))
    #seriesInfo = tvdb.get_series_all(metadata.getId(), banners=False)
    seriesInfo = tvdb.get_series_details(metadata.getId())
    cover = "http://thetvdb.com/banners/%s" % seriesInfo['poster']
    if seriesInfo['fanart'] is not None and len(seriesInfo['fanart']) > 0:
      metadata.fanart("http://thetvdb.com/banners/%s" % seriesInfo['fanart'])
    log.debug("Loaded details: %s" % str(seriesInfo))
    cast = seriesInfo['actors']
    try:
      metadata.rating(float(seriesInfo['rating']))
    except:
      log.warning("Could not parse rating from '%s'" % str(seriesInfo['rating']))
    firstAired = seriesInfo['first_aired']
    if firstAired:
      firstAired = firstAired.date()
    metadata.studio(seriesInfo['network']).cover(cover)
    metadata.title(seriesInfo['name']).plot(seriesInfo['overview']).plotoutline(seriesInfo['overview']).premiered(str(firstAired))
    metadata.genre(", ".join(seriesInfo['genre'])).duration(seriesInfo['runtime']).cast(cast)
    return seriesInfo
  
  def loadEpisode(self, metadata):
    season_num = metadata.getSeason()
    episode_num = metadata.getEpisode()
    tvshow_id = metadata.getTvShowId()
    log.debug("Loading details for tv show episode id: %s" % str(tvshow_id))
    episode = tvdb.get_episode(tvshow_id, season_num, episode_num)
    log.debug("Loading details: %s" % str(episode))
    episodeId = episode['id']
    episodename = episode["name"]
    firstAired = episode['first_aired']
    if firstAired:
      firstAired = firstAired.date()
    metadata.title(episodename).season(episode['season_number']).episode(episode['episode_number'])
    metadata.plot(episode["overview"]).premiered(str(firstAired)).code(episodeId)
    if settings.isSet("load-episode-cover") and episode["image"]:
      cover = "http://thetvdb.com/banners/%s" % episode["image"]
      metadata.cover(cover) 
    log.debug("Created episode metadata from TVDB: %s" % metadata)
    return metadata
  
class MovieMetadataLoader(MetadataLoader):
  def searchMovie(self, title):
    log.info("Searching TMDB...")
    searchResults = tmdb.search(title)
    log.debug("Found movies '%s'" % str(searchResults))
    return self.choose(searchResults, "Select movie by title")
  
  def loadMovie(self, metadata):
    details = tmdb.getMovieInfo(metadata.getId())
    metadata.plot(details['overview']).plotoutline(details['overview'])
    if details.has_key('runtime'):
      metadata.duration("%s minutes" % details['runtime'])
    if details.has_key('studios'):
      metadata.studio(", ".join([studio for studio in details['studios'].keys()]))
    if details.has_key('categories') and details['categories'].has_key('genre'):
      metadata.genre(", ".join([cat for cat in details['categories']['genre'].keys()]))
    if details.has_key('cast'):
      cast = details['cast']
      if cast.has_key('director'):
        metadata.director(", ".join([director['name'] for director in cast['director']]))
      if cast.has_key('screenplay'):
        metadata.writer(", ".join([writer['name'] for writer in cast['screenplay']]))
      if cast.has_key('actor'):
        metadata.cast([actor['name'] for actor in cast['actor']])
    if details .has_key('rating'):
      try:
        metadata.rating(float(details['rating']))
      except:
        log.warning("Could not parse rating from '%s'" % str(details['rating']))
    if details.has_key('released'):
      metadata.premiered(details['released'])
      try:
        import time
        metadata.year(time.strptime(details['released'], "%Y-%m-%d")[0])
      except:
        log.exception("Could not parse year")
    if details.has_key('images'):
      posters = details['images'].posters
      backdrops = details['images'].backdrops
      if len(posters) > 0:
        metadata.cover(posters[0]['cover'])
      if len(backdrops) > 0:
        metadata.fanart(backdrops[0]['poster'])
        
    log.debug("Found movie metadata from TMDB: %s" % str(metadata))

class MetadataProvider(MovieMetadataLoader, TvDbMetadataLoader):
  def search(self, entry):
    """Search the online metadata provider for an entry
    @param entry: the MetadataKey to search metadata for
    @return: the movie id or None if not found/cancelled""" 
    if entry.isTVShow() or entry.isAnime():
      return self.searchTvShow(entry.getName())
    elif entry.isMovie():
      return self.searchMovie(entry.getName())
    else:
      raise NotImplementedError("Only supported searching for Tv Shows or movies")

  def load(self, entry, metadata):
    """
    Load the metadata.
    For all types, metadata should contain the "code" entry to identify it's record
    in the online database. For Tv show episodes, the metadata should also contain the
    season number and episode number to be loaded
    
    @param entry: the entry to load metadata for
    @param metadata: the metadata builder to load metadata into
    """ 
    if entry.isTVShow():
      return self.loadTvShow(metadata)
    elif entry.isEpisode():
      return self.loadEpisode(metadata)
    if entry.isMovie():
      return self.loadMovie(metadata)
      
