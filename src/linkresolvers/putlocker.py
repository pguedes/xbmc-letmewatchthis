'''support for putlocker media host

This module implements the interface of a LinkResolver

This code is based on some code found online from an anonymous author (http://pastebin.com/q7wiCpey)

To resolve a link in putlocker, we do the following:
 - if we have login details, we login to get auth cookies. 
 - Otherwise we parse the hash from the form in the page and post the 'Continue as Free User' like the user would
 - after this we do a request to the rss feed to load the url of the stream 

Created on Nov 26, 2011

@author: pguedes'''
import re, logging
from utils.htmlutils import HttpClient
from time import sleep
from utils import notification

COOKIES_FILE = 'putlocker-cookies.lwp'

log = logging.getLogger("linkresolver.putlocker")

class PutLockerLinkResolver:

    def __init__(self):
        self.__httpClient = None
        self.__loggedIn = False

    def isLoggedIn(self):
        return self.__loggedIn

    def getHttpClient(self):
        if not self.__httpClient:
            self.__httpClient = HttpClient(True)
        return self.__httpClient

    def resolve(self, url):
        if url.find('putlocker') < 0:
            raise Exception("not a putlocker link")

        notifier = notification.getUserNotifier('PutLocker', 'Initializing resolver...')

        http = self.getHttpClient()

        try:

            # login to use pro account
            if not self.isLoggedIn():
                from utils import pluginsupport, settings

                username = settings.get("putlocker-user")
                password = settings.get("putlocker-pass")

                if username and password and not self.isLoggedIn():
                    loginData = pluginsupport.encodeArgs({'user': username, 'pass': password, 'login_submit': 'Login'})
                    notifier.update(20, "performing login for premium link...")
                    log.debug("loggin in '%s' to pulocker.com" % str(username))
                    http.get('http://www.putlocker.com/authenticate.php?login', data=loginData)
                    notifier.update(30, "logged in...")
                    self.__loggedIn = True
                    log.debug("logged in? '%s'" % str(self.isLoggedIn()))
                else:
                    # find session hash
                    notifier.update(0, "getting page to parse session hash...")
                    page = http.get(url)
                    hash = re.search('value="([0-9a-f]+?)" name="hash"', page).group(1)
                    notifier.update(10, "got hash '%s'... waiting 5 seconds to POST..." % hash)
                    log.info('now waiting 5 seconds to post confirmation data...')
                    for i in range(0, 5):
                        sleep(1)
                        log.info(i + 1)

                    postData = pluginsupport.encodeArgs({'hash': hash, 'confirm': 'Continue as Free User'})
                    notifier.update(40, "done waiting... now POSTing hash '%s'..." % hash)
                    log.debug("posting hash and confirmation for free user: '%s'" % str(postData))
                    page = http.get(url, data=postData)

            notifier.update(50, "getting rss feed url from page")
            page = http.get(url)
            rssFeedUrl = 'http://www.putlocker.com' + re.search("playlist: '(/get_file.php.+?)'", page).group(1)
            # get the rss feed xml to load the video stream location from
            notifier.update(70, "requesting rss feed xml from '%s'" % rssFeedUrl)
            log.debug("now loading rss feed xml. url is '%s'" % str(rssFeedUrl))
            page = http.get(rssFeedUrl)

            mediaUrlMatch = re.search('url="(.+?)"', page)
            if mediaUrlMatch:
                resolvedUrl = mediaUrlMatch.group(1)
                if url.find('expired_link'):
                    raise Exception("link is expired")
                notifier.update(90, "resolved url to play: '%s'" % resolvedUrl)
                log.debug("found stream link: '%s'" % resolvedUrl)
                return resolvedUrl

        finally:
            notifier.close()

        log.debug("url not found for putlocker...")
