# -*- coding: UTF-8 -*-
import plugin
import logging
import sys

plugin.initialize('plugin.video.primewire', 'primewire')

log = logging.getLogger("root")
log.info("calling with args: %s" % str(sys.argv))

try:
    plugin.handle()
except:
    log.exception("Failed to handle request")
