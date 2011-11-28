#!/bin/sh
cd src/ && zip -q -r /tmp/xbmc-letmewatchthis.zip * -x */*.svn/*
if [ 0 -eq $? ]; then
	echo "Package created in /tmp/xbmc-letmewatchthis.zip"
else
    echo "Could not create package!"
fi
