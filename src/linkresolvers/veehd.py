'''
Created on Dec 5, 2010

@author: pedro
'''
from resolverUtils import regexFinder, processSourcePage

def resolve(page):
  return processSourcePage(page, regexFinder('<embed type="video/divx" src="(.+?)"'))

    
  