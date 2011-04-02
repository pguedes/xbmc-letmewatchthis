# -*- coding: UTF-8 -*-
'''
Support for youtube links

Created on Apr 6, 2010

@author: pguedes
'''
from yt import GetYouTubeVideo
import re, logging

log = logging.getLogger('youtube')

def resolve(page):
  id = re.compile('src="http://www.youtube.com/v/(.+)"').findall(page)[0]
  id = id.split('&')[0]
  log.debug("Youtube video id: %s" % str(id))
  youtubeUrl = "http://www.youtube.com/watch?v=%s" % id
  log.debug("Youtube video url: %s" % str(youtubeUrl))
  resolved = GetYouTubeVideo(youtubeUrl)
  log.debug("resolved youtube video '%s' to url: %s" % (id, resolved))
  return [resolved]
  
