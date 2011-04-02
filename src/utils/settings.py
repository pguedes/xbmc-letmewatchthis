'''
Created on Jul 25, 2010

@author: pedro
'''
import sys, xbmcplugin

def get(setting):
#  return xbmcplugin.getSetting(setting);
  # Dharma settings...
  return xbmcplugin.getSetting(int(sys.argv[1]), setting);

def isSet(setting):
  return get(setting) == "true";