'''
Created on Dec 5, 2010

@author: pedro
'''
from resolverUtils import regexFinder, processSourcePage
import utils.htmlutils as http

def resolve(page):
  aiv = regexFinder('var aiv = (.+?);')(page)[0]
  internalpage = http.get("http://www.tvdex.org/includes/ajax/video_loader.php?episode_id="+aiv, True)
  return processSourcePage(internalpage, regexFinder('flashvars\.file="(.+)";'))

    
