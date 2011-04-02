#!/bin/bash
rm -rf ~/.xbmc/addons/plugin.video.letmewatchthis/*
cp -r src/* ~/.xbmc/addons/plugin.video.letmewatchthis
mv ~/.xbmc/addons/plugin.video.letmewatchthis/resources/logging-debug.conf ~/.xbmc/addons/plugin.video.letmewatchthis/resources/logging.conf
