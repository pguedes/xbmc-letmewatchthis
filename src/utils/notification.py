# -*- coding: UTF-8 -*-
'''
User progress notification utils.

A user notifier is an object that knows how to comunicate progress
to the user.

Use the factory method getUserNotifier to get a UserNotifier according
to the plugin's settings. 

Created on Apr 2, 2010

@author: pguedes
'''
import xbmc, xbmcgui #@UnresolvedImport
from utils import settings

METHOD_PROGRESS, METHOD_NATIVE, METHOD_OFF = "0", "1", "2"

def getUserNotifier(title, initialMessage):
  """Factory method to create a user notifier according to xbmc-tvshack plugin settings
  @param title: the title to initialize the notifier with
  @param initialMessage: the initial message to display"""
  setting = settings.get("notification-method")
  if setting == METHOD_PROGRESS:
    return ProgressDialogNotifier(title, initialMessage)
  elif setting == METHOD_NATIVE:
    return UserNotificationNotifier(title, initialMessage)
  else:
    return NullNotifier()

class UserNotifier:
  def update(self, percentage, message):
    """Update the message shown to the user
    @param percentage: the progress percentage to update with
    @param message: the message to show"""
    pass
  def close(self):
    """Close/hide the UserNotifier"""
    pass

class NullNotifier(UserNotifier):
  """A notifier that does nothing.""" 
  pass  

class ProgressDialogNotifier:
  '''Creates a progress dialog to show information'''
  def __init__(self, title, initialMessage):
    self.__dialog = xbmcgui.DialogProgress()
    self.__dialog.create(title, initialMessage)
    
  def update(self, percentage, message):
    self.__dialog.update(percentage, message)
    
  def close(self):
    self.__dialog.close()
    
class UserNotificationNotifier:
  '''Uses the internal XBMC notification to send user information messages'''
  def __init__(self, title, initialMessage):
    self.__title = title
    xbmc.executebuiltin("Notification(%s,%s,-1)" % (title, initialMessage))
    
  def update(self, percentage, message):
    xbmc.executebuiltin("Notification(%s,%s,-1)" % (self.__title, message))

  def close(self):
    xbmc.executebuiltin("Notification(%s,Done,1000)" % self.__title)

