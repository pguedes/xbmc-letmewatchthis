'''
Created on May 31, 2010

@author: pedro
'''
from resolverUtils import regexFinder

def resolve(page):
  return regexFinder('flashvars\.file="(.+)";')(page)

    
