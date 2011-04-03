"""PyTVDB is a python interface to TheTVDB.com's web API.
Copyright (c) 2009, Andre LeBlanc <andrepleblanc@gmail.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY <copyright holder> ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <copyright holder> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


from BeautifulSoup import BeautifulStoneSoup
from datetime import datetime
from zipfile import ZipFile
import urllib, urllib2
import time

API_KEY = "0629B785CE550C8D"

_LANGUAGE = "en"


BASE_URL = "http://www.thetvdb.com/"
ONE_DAY = 86400 #seconds.

# Internal Utility Functions.
def _s2date(s):
    """Convert a string representation of a date into a datetime object."""
    y, m, d = s.split("-")
    return datetime(int(y), int(m), int(d))

def _g(soup, tag_name, wrapper_func=None, default=None):
    """Extract the value from the tag named tag_name."""
    if not wrapper_func:
        wrapper_func = unicode
    node = soup.find(tag_name)
    if node and node.contents:
        return wrapper_func(node.contents[0])
    else:
        return default

def _parse_partial_series(soup):
    """Parse partial series soup (from search results), return a dict."""
    s = dict(id=_g(soup, 'id', int),
             language=_g(soup, 'language'),
             name=_g(soup, 'seriesname'),
             banner=_g(soup, 'banner'),
             overview=_g(soup, 'overview'),
             first_aired=_g(soup, 'first_aired', _s2date),
             imdb_id=_g(soup, 'imdb_id'),
             zap2it_id=_g(soup, 'zap2it_id'))
    return s

def _parse_series(soup):
    """Parse a complete series listing."""
    s = _parse_partial_series(soup)
    s.update(dict(airs_days=_g(soup, "airs_dayofweek"),
                  airs_time=_g(soup, "airs_time"),
                  content_rating=_g(soup, "contentrating"),
                  genre=_g(soup, "genre", lambda genre: [g for g in genre.split("|") if g]),
                  network=_g(soup, 'network'),
                  rating=_g(soup, 'rating'),
                  runtime=_g(soup, 'runtime'),
                  status=_g(soup, 'status'),
                  fanart=_g(soup, 'fanart'),
                  last_updated=_g(soup, 'lastupdated', int),
                  poster=_g(soup, 'poster')))
    return s

def _parse_series_actors(soup):
    """Parse a complete series listing."""
    s = _parse_partial_series(soup)
    s.update(dict(airs_days=_g(soup, "airs_dayofweek"),
                  airs_time=_g(soup, "airs_time"),
                  content_rating=_g(soup, "contentrating"),
                  genre=_g(soup, "genre", lambda genre: [g for g in genre.split("|") if g]),
                  actors=_g(soup, "actors", lambda actors: [g for g in actors.split("|") if g]),
                  network=_g(soup, 'network'),
                  rating=_g(soup, 'rating'),
                  runtime=_g(soup, 'runtime'),
                  status=_g(soup, 'status'),
                  fanart=_g(soup, 'fanart'),
                  last_updated=_g(soup, 'lastupdated', int),
                  poster=_g(soup, 'poster')))
    return s

def _parse_episode(soup):
    """Parse an episode listing. Return a dict"""
    e = dict(id=_g(soup, 'id', int),
             combined_episode_number=_g(soup, 'combined_episodenumber'),
             combined_season=_g(soup, 'combined_season', int),
             dvd_chapter=_g(soup, 'dvd_chapter', int),
             dvd_disc_id=_g(soup, 'dvd_discid'),
             dvd_episode_number=_g(soup, 'dvd_episodenumber'),
             dvd_season=_g(soup, 'dvd_season', int),
             director=_g(soup, 'director'),
             name=_g(soup, 'episodename'),
             episode_number=_g(soup, 'episodenumber', int),
             first_aired=_g(soup, 'firstaired', _s2date),
             gueststars=_g(soup, 'gueststars', lambda stars: [s for s in stars.split("|") if s]),
             imdb_id=_g(soup, 'imdb_id'),
             language=_g(soup, 'language'),
             overview=_g(soup, 'overview'),
             production_code=_g(soup, 'productioncode'),
             rating=_g(soup, 'rating'),
             season_number=_g(soup, 'seasonnumber', int),
             writer=_g(soup, 'writer'),
             absolute_number=_g(soup, 'absolute_number', int),
             airs_after_season=_g(soup, 'airsafter_season', int),
             airs_before_episode=_g(soup, 'airsbefore_episode', int),
             airs_before_season=_g(soup, 'airsbefore_season', int),
             last_updated=_g(soup, 'lastupdated', int),
             season_id=_g(soup, 'seasonid', int),
             image_flag=_g(soup, 'epimgflag', int),
             image=_g(soup, 'filename'))
    return e

def _parse_actor(soup):
    """Parse an Actor, return a dict"""
    a = dict(id=_g(soup, 'id', int),
             image=_g(soup, 'image'),
             name=_g(soup, 'name'),
             role=_g(soup, 'role'),
             sort_order=_g(soup, 'sortorder', int))
    return a

def _parse_banner(soup):
    """Parse a banner, return a dict"""
    b = dict(id=_g(soup, 'id', int),
             path=_g(soup, 'bannerpath'),
             type=_g(soup, 'bannertype'),
             type2=_g(soup, 'bannertype2'),
             colors=_g(soup, 'colors', lambda cstr: [tuple([int(i) for i in c.split(",")]) for c in cstr.split("|") if c]),
             language=_g(soup, 'language'),
             thumbnail_path=_g(soup, 'thumbnailpath'),
             vignette_path=_g(soup, 'vignettepath'))
    if 'season' in (b['type'], b['type2']):
        b['season'] = _g(soup, 'season', int)
        
    return b
             
             

# Official API Starts here.

def get_languages():
    """Return a list of languages supported by the server

    Returns a list of dicts each having 'name', 'abbreviation', 
    and 'id' keys.
    
    """
    url = "%s/api/%s/languages.xml" % (BASE_URL, API_KEY)
    soup = BeautifulStoneSoup(urllib2.urlopen(url).read())
    languages = []
    for lang in soup.languages.findAll("language"):
        languages.append({'name': _g(lang, 'name'),
                          'abbreviation': _g(lang, 'abbreviation'),
                          'id': _g(lang, 'id', int)})
    return languages


def set_language(language_abbr):
    """Set the language to be used for all future queries"""
    _LANGUAGE = language_abbr
    

def get_series(series_name_search):
    """Return all possible matches for series_name_search in the chosen language
    
    
    """
    url = "%sapi/GetSeries.php?seriesname=%s&language=%s" % (BASE_URL, urllib.quote(series_name_search), _LANGUAGE)
    soup = BeautifulStoneSoup(urllib2.urlopen(url).read())
    matches = []
    for series in soup.data.findAll("series"):
        matches.append(_parse_series(series))
    return matches

def get_series_details(series_id):
    """Returns details on a single series, not including banners/episodes)"""
    url = "%sapi/%s/series/%s/%s.xml" % (BASE_URL, API_KEY, series_id, _LANGUAGE)    
    soup = BeautifulStoneSoup(urllib2.urlopen(url).read())
    return _parse_series_actors(soup.data)

def get_episode_by_id(episode_id):
    """Returns details on a single episode"""
    url = "%sapi/%s/episodes/%s/%s.xml" % (BASE_URL, API_KEY, episode_id, _LANGUAGE)    
    soup = BeautifulStoneSoup(urllib2.urlopen(url).read())
    return _parse_episode(soup.data)
    
def get_episode(seriesId, season_num, episode_num):
    """Returns details on a single episode by it's series id, season and episode numbers"""
    url = "%sapi/%s/series/%s/default/%s/%s/%s.xml" % (BASE_URL, API_KEY, seriesId, season_num, episode_num, _LANGUAGE)    
    soup = BeautifulStoneSoup(urllib2.urlopen(url).read())
    return _parse_episode(soup.data)      

def get_series_all(series_id, episodes=True, banners=True, actors=True):
    """Return all available data for a series."""
    url = "%sapi/%s/series/%s/all/%s.zip" % (BASE_URL, API_KEY, series_id, _LANGUAGE)
    print url
    filename, headers = urllib.urlretrieve(url)
    zf = ZipFile(file(filename))
    soup = BeautifulStoneSoup(zf.read("%s.xml" % (_LANGUAGE,)))
    series = _parse_series(soup.find('series'))
    if episodes:
        series['episodes'] = [_parse_episode(e) for e in soup.findAll('episode')]
    
    if actors:
        soup = BeautifulStoneSoup(zf.read("actors.xml"))
        series['actors'] = [_parse_actor(a) for a in soup.findAll('actor')]

    if banners:
        soup = BeautifulStoneSoup(zf.read("banners.xml"))
        series['banners'] = [_parse_banner(b) for b in soup.findAll('banner')]

    return series

def get_updates(since, for_series_ids=None):
    """Returns  all updates since 'since'. optionally filtering on series id"""
    if isinstance(since, datetime):
        since = time.mktime(since.timetuple())

    now = time.time()
    if since - now > ONE_DAY * 30:
        interval = 'all'
    elif since - now > ONE_DAY * 7:
        interval = 'month'
    elif since - now > ONE_DAY:
        interval = 'week'
    else:
        interval = 'day'
        
    url = "%sapi/%s/updates/updates_%s.zip" % (BASE_URL, API_KEY, interval)
    filename, headers = urllib.urlretrieve(url)
    zf = ZipFile(file(filename))
    soup = BeautifulStoneSoup(zf.read('updates_%s.xml' % (interval,)))
    last_update = int(soup.data['time'])
    soup = soup.data
    def _parse_series_update(soup):
        d = dict(id=_g(soup, 'id', int),
                 time=_g(soup, 'time', int))
        if d['time'] > since and (for_series_ids is None or d['id'] in for_series_ids):
            return d
        return None
    def _parse_episode_update(soup):
        d = dict(id=_g(soup, 'id', int),
                 series=_g(soup, 'series', int),
                 time=_g(soup, 'time', int))
        if d['time'] > since and (for_series_ids is None or d['series'] in for_series_ids):
            return d
        return None
    def _parse_banner_update(soup):
        d = dict(series=_g(soup, 'series', int),
                    format=_g(soup, 'format'),
                    language=_g(soup, 'language'),
                    time=_g(soup, 'time', int),
                    path=_g(soup, 'path'),
                    type=_g(soup, 'type'))
        if d['time'] > since and (for_series_ids is None or d['series'] in for_series_ids):
            return d
        return None
    def _for_series(id):
        return for_series_ids is None or id in for_series_ids

    return dict(series=filter(None, [_parse_series_update(s) for s in soup.findAll('series', recursive=False)]),
                banners=filter(None, [_parse_banner_update(b) for b in soup.findAll('banner', recursive=False)]),
                episodes=filter(None, [_parse_episode_update(e) for e in soup.findAll('episode', recursive=False)]))
    
