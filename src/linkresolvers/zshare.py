'''
Resolves zshare links

Created on Mar 27, 2010

@author: pguedes
'''
import base64, utils.htmlutils as http
import re, logging

log = logging.getLogger("zshare")

def resolve(page):
  tweety = re.compile("(http://tweetypie.tvshack.cc/zs/\?id=.+?)'").findall(page)
  log.debug("Got tweetypie page: %s" % str(tweety[0]))
  # get the redirect url from headers
  downloadLink = http.get(tweety[0], returnResponse=True).url
  log.debug("Got zshare player page: %s" % str(downloadLink))
  downloadLink = "http://127.0.0.1:64653/zshare/%s" % base64.urlsafe_b64encode(downloadLink)
  log.debug("Resolved to proxied url: %s" % str(downloadLink))
  return [downloadLink]
