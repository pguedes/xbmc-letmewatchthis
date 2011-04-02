'''
Created on May 31, 2010

@author: pedro
'''
from resolverUtils import processSourcePage, regexFinder 

def resolve(page):
  return processSourcePage(page, regexFinder('flashvars\.file="(.+)";'))
    
