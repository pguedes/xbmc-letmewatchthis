# -*- coding: UTF-8 -*-
import logging.config, os, sys
configRoot = os.path.join(os.getcwd(), "resources", "logging.conf")
try:
  logging.config.fileConfig(configRoot)
except:
  logging.basicConfig()
  logging.getLogger('root').exception('Failed to initialize logging... falling back to defaults.')

# Add the lib dir to path  
sys.path.append(os.path.join(os.getcwd(), 'lib'))

#
# There is probably a better way to do this... 
# letmewatchthis is the handler module which registers it's mode/action handler functions with the plugin
# module which then can handle plugin requests from the mode/action handler registry
import letmewatchthis, plugin

log = logging.getLogger("root")
log.info("calling with args: %s"%str(sys.argv))

try:
  plugin.handle()
except:
  log.exception("Failed to handle request")
