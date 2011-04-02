'''
Resolves tweetiepie links

Created on Mar 27, 2010

@author: pguedes
'''
import re, logging, utils.htmlutils as http

log = logging.getLogger("tweety")

def resolve(page):
  tweety = re.compile('flashvars="file=(.+?)&type=flv').findall(page)
  # follow redirects to get the final url
  url = http.get(tweety[0], returnResponse=True).url
  log.debug("Resolved tweetypie: %s" % str(url))
  # run veoh streams through proxy
  if url.find('veoh') > 0:
    import base64
    url = "http://127.0.0.1:64653/veoh/%s" % base64.urlsafe_b64encode(url)
    log.debug("Returning proxied veoh stream: %s" % str(url))
  return [url]
