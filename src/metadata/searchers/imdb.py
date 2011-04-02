import re, urllib
import utils.htmlutils as http
import logging

log = logging.getLogger("imdb")

def query(name):
  log.info("searching for '%s'" % name)  
  response = http.get('http://www.imdb.com/find?s=all&q=' + urllib.quote(name))
  log.debug("search(%s): %s" % (name, response))
  imdbIDs = re.compile('<b>Media from&nbsp;<a href="/title/(.+?)/"').findall(response)
  if len(imdbIDs) > 0:
    return __harvest(imdbIDs[0])
  else :
    imdbIDs = re.compile(r'<link rel="canonical" href="http://www.imdb.com/title/(.+)/"').findall(response)
    if len(imdbIDs) < 1:
      imdbIDs = re.compile(r'<a name="poster" href="/.+?/.+?/.+?-photo/media/.+?/(.+?)" title=".+?">').findall(response)
    if len(imdbIDs) > 0:
      return __harvest(imdbIDs[0], response)
    log.warning("No match found for title '%s'" % name)

def __harvest(imdbId, html=None):
  def find(regex, html, mode=0, convert=""):
    found = re.compile(regex, mode).findall(html)
    if len(found) >= 1:
      if convert == "int":
        try: return int(found[0])
        except: return 0      
      if convert == "float":
        try: return float(found[0])
        except: return 0.0      
      return found[0]
    return "Not Found"
  
  if html == None:
    html = http.get('http://imdb.com/title/' + imdbId)
    
  genre = find(r'<h5>Genre:</h5>.+?<a href=".+?">(.+?)</a>', html, re.DOTALL)
  year = find(r'<a href="/Sections/Years/.+?/">(.+?)</a>', html, convert="int")
  image = find(r'<img border="0" alt=".+?" title=".+?" src="(.+?)" /></a>', html)
  rating = find(r'<div class="starbar-meta">.+?<b>(.+?)/10</b>', html, re.DOTALL, convert="float")
  director = find(r'<h5>Director:</h5>.+?<a href=".+?">(.+?)</a>', html, re.DOTALL)
  writer = find(r'<h5>.Writer.+?:.+?</h5>.+?<div class="info-content">.+?<a href=".+?".+?>(.+?)</a>.+?</div>', html, re.DOTALL)
  runtime = find(r'<h5>Runtime:</h5>.+?<div class="info-content">\n(.+? min).+?</div>', html, re.DOTALL)
  votes = find(r'<a href="ratings" class="tn15more">(.+?) votes</a>', html, re.DOTALL)
  #actorandrole = re.compile(r'<a href="/name/nm.+?>([A-Za-z ]+?)</a>.+?</td>.+?<td class="char">.+?<a href="/character/ch.+?>([A-Za-z ]+?)</a>', re.DOTALL).findall(html)
  actorandrole = re.compile(r'<a href="/name/nm.+?>([A-Za-z ]+?)</a>', re.DOTALL).findall(html)
  cast = []
  for actor in actorandrole:
    cast.append(actor)
  
  html = http.get('http://www.imdb.com/title/' + imdbId + '/plotsummary')
  plot = find('<p class="plotpar">\n(.+?)\n<i>\n', html)
  log.debug("found so far(1): %s, %s, %s, %s, %s, %s, %s, %s, %s" % (genre, year, image, rating, plot, director, writer, runtime, str(cast)))
  try:
    if plot.find('div') == 1:
      plot = 'No Plot found on Imdb'
  except: 
    log.warning("Could not load plot for (IMDB:%s)" % imdbId)

  if len(plot) < 1:
    plotter = http.get('http://www.imdb.com/title/' + imdbId + '/synopsis')
    clean = re.sub('\n', '', plotter)
    plot = find('<div id="swiki.2.1">(.+?)</div>', clean)
    try:
      if plot.find('div') > 0:
        plot = 'No Plot found on Imdb'
    except:
      log.warning("Could not load plot for (IMDB:%s)" % imdbId)
          
  log.debug("returning: %s, %s, %s, %s, %s, %s, %s, %s, %s" % (genre, year, image, rating, plot, director, writer, runtime, str(cast)))
  log.info("finished searching")
  return genre, year, image, rating, plot, director, writer, runtime, cast, votes, imdbId
