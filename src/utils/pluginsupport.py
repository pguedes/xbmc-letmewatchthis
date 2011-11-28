#  -*-  coding:  UTF-8  -*-
'''
Created  on  Jan  24,  2010

@author:  pguedes
'''
from  utils  import  notification
import  xbmc, xbmcplugin, xbmcgui  #@UnresolvedImport
import  urllib, os, sys, logging

log = logging.getLogger("pluginsupport")

CACHE_PATH_FORMAT = "special://masterprofile/Thumbnails/Video/%s/%s"

def _preChacheThumbnail(url, reason="May  take  a  while..."):
    '''Cache  an  image  file  (cover  or  backdrop)
    @param  url:  the  url  of  the  image  file  to  cache  locally
    @param  reason:  the  reason  to  inform  the  user  with,  since  this  is  may  take  a  while
    @return:  the  path  to  the  file  cached  locally'''
    if  url  is  None  or  url == "":  return  ""
    try:
        filename = xbmc.getCacheThumbName(url)
        filepath = CACHE_PATH_FORMAT % (filename[0], filename)
        log.debug("Got thumbnail path '%s' for file '%s'" % (filename, url))
        if  not  os.path.isfile(filepath):
            notifier = notification.getUserNotifier("Downloading  artwork", reason)
            log.debug("Caching  thumbnail  '%s'  for  remote  file  '%s'" % (filename, url))
            urllib.urlretrieve(url, filepath)
            urllib.urlcleanup()
            notifier.close()
        log.debug("Returning  thumb  '%s'  for  file  '%s'" % (filename, url))
        return  filepath
    except:
        log.exception("Failed  to  cache  thumbnail:  %s" % url)
        return  url

def select(title, items):
    log.debug("showing options to user: '%s'" % str(items))
    return xbmcgui.Dialog().select(title, items)

def showError(e, errorMessage='An  error  occurred!'):
    xbmcgui.Dialog().ok('Error', errorMessage, str(e))

def list(result, contentType=None):
    """List some PluginMovieItems in XBMC
    @param listItems: an iterable of PluginMovieItem instances"""
    count = result.size
    items = callable(result.items)  and  result.items()  or  result.items
    for item in items:
        targetUrl = item.getTargetUrl()
        listItem = item.getListItem()
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), targetUrl, listItem, not  item.isPlayable(), count)
    if contentType:
        log.warn("Setting content type: " + str(contentType))
        xbmcplugin.setContent(int(sys.argv[1]), contentType)

def play(playableItems):
    if playableItems  and  len(playableItems) > 1:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        #  we  need  to  append  the  parts  to  the  playlist
        log.debug("Playing  items:  %s" % str(playableItems))
        position = playlist.getposition()
        otherParts = playableItems[1:]
        try:
            for  index  in  range(len(otherParts)):
                playable = otherParts[index]
                partNumber = index + 2
                log.debug("Appending  part  %s:  %s  %s" % (str(partNumber), playable.getTargetUrl(), str(position + partNumber)))
                playlist.add(playable.getTargetUrl(), playable.getListItem(), position + partNumber)
                log.debug("Appended  part  %s:  %s" % (str(partNumber), playable.getTargetUrl()))
        except:
            log.exception("Failed  adding  items  to  playlist")

    log.debug("setting  resolved  url:  %s" % playableItems[0].getTargetUrl())
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, playableItems[0].getListItem())

def  done(success=True):
    xbmcplugin.endOfDirectory(int(sys.argv[1]), success)

def  getArguments():
    '''Parse  the  URL  arguments  into  a  map
    @return:  a  dict  with  the  arguments'''
    param = {}
    paramstring = sys.argv[2]
    if  len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if  (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        for  i  in  range(len(pairsofparams)):
            splitparams = pairsofparams[i].split('=')
            if  (len(splitparams)) == 2:
                param[splitparams[0]] = urllib.unquote_plus(splitparams[1])
    return  param


def  encodeArgs(paramMap):
    '''Encode  a  list  of  params  into  a  post string
    @param  paramMap:  map  of  params  to  encode  into  post string
    @return:  encoded  url  (<arg1=arg1Val>&...)'''
    params = ["%s=%s" % (key, urllib.quote_plus(value))  for  key, value  in  paramMap.items()]
    return  "&".join(params)

def  encodeURLWithProtocolParameters(baseUrl, paramMap):
    '''Create a special url that contains protocol parameters (User-Agent, Cookie, etc) to pass to XBMC's player
    @param baseUrl: the target url for the player
    @param  paramMap:  map  of  protocol parameters that the player should use to open the stream
    @return:  encoded  url with player parameters (<url>|<protocolParams>)'''
    return "%s|%s" % (baseUrl, encodeArgs(paramMap))

def  encode(paramMap):
    '''Encode  a  list  of  params  into  a  url
    @param  paramMap:  map  of  params  to  encode  into  url
    @return:  encoded  url  (<base>?<arg1=arg1Val>&...)'''
    return  sys.argv[0] + "?" + encodeArgs(paramMap)
