#!/bin/bash
rm -rf ~/.xbmc/addons/plugin.video.primewire/*
cp -r src/* ~/.xbmc/addons/plugin.video.primewire
mv ~/.xbmc/addons/plugin.video.primewire/resources/logging-debug.conf ~/.xbmc/addons/plugin.video.primewire/resources/logging.conf
