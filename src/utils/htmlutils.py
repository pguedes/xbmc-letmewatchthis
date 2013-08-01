# -*- coding: UTF-8 -*-
import re, urllib2
import logging

log = logging.getLogger("htmlutils")

class HttpClient(object):
    '''an HTTP client facade to handle the http interface required by linkresolvers.
    This client supports cookies via cookielib.'''
    def __init__(self, useCookies=False):
        '''create a new http client.
        @param useCookies: if the client should support cookies
        @return: true if this client uses cookies, false otherwise'''
        if useCookies:
            self.__setupCookieHandling()
        else:
            self.opener = urllib2.urlopen

    def usesCookies(self):
        '''check if this http client uses cookies.
        @return: true if this client uses cookies, false otherwise'''
        return self.cookieJar is not None;

    def loadCookies(self, file):
        '''loads cookies for this client from a file.
        @param file: the file to load cookies from'''
        import os
        if os.path.isfile(file):
            log.debug("loading cookies from file '%s'" % file)
            self.cookieJar.load(file)

    def getCookiesAsHeaderString(self):
        '''get the cookies stored in this client as a string that can be used in an http header
        @return: a string representation of the cookies in this clients cookie jar'''
        if self.cookieJar:
            return "; ".join(["%s=%s" % (cookie.name, cookie.value) for cookie in self.cookieJar])

    def saveCookies(self, file, skipDiscard=False):
        '''save the cookies in this client's cookie jar to a file.
        @param file: the file to save cookies to
        @param skipDiscard: if discarded cookies should still be saved'''
        if self.cookieJar:
            self.cookieJar.save(file, ignore_discard=skipDiscard)

    def __setupCookieHandling(self, cookiesFile=None):
        '''creates a cookie jar, loads the cookies from a file and sets up the urllib2 opener to keep track 
        of cookies on requests done by this client.
        @param cookiesFile: the file with cookies to load
        @return: the cookie jar loaded'''
        import cookielib

        self.cookieJar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))

    def resolveRedirect(self, url):
        return self.get(url, returnResponse=True).url

    def get(self, url, ajax=False, cleanup=False, data=None, returnResponse=False, extraHeaders=None):
        '''Load a webpage from with an HTTP request like a browser would do
        @param ajax: if True, will add header to identify to server as an XMLHttpRequest (from a browser)
        @param cleanup: if True, data will be cleaned up before returning
        @param data: data to be POSTed on the request
        @param returnResponse: if True, will return the response object before reading instead of data read
        @return: the loaded html, or the response if returnResponse was true'''
        target = getTarget(url)

        req = urllib2.Request(target)
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')
        if ajax:
            req.add_header('X-Requested-With', 'XMLHttpRequest')

        if extraHeaders:
            for header, headerval in extraHeaders.iteritems():
                req.add_header(header, headerval)

        log.debug("Getting target '%s' (original: %s)" % (target, url))
        response = self.opener.open(req, data)
        log.debug("Getting target '%s' (original: %s)" % (target, url))

        if returnResponse:
            return response

        html = response.read()
        response.close()

        if cleanup:
            html = cleanHtml(html)

        return html

def resolveRedirect(url):
    return get(url, returnResponse=True).url

def get(url, ajax=False, cleanup=False, data=None, returnResponse=False, extraHeaders=None, cookies=None):
    '''Load a webpage from with an HTTP request like a browser would do
    @param ajax: if True, will add header to identify to server as an XMLHttpRequest (from a browser)
    @param cleanup: if True, data will be cleaned up before returning
    @param data: data to be POSTed on the request
    @param returnResponse: if True, will return the response object before reading instead of data read
    @param cookies: a cookies file to use to store cookies for a request
    @return: the loaded html, or the response if returnResponse was true'''
    target = getTarget(url)

    cookieJar = None
    if cookies:
        cookieJar = setupCookiesForRequest(cookies)

    req = urllib2.Request(target)
    req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')
    if ajax:
        req.add_header('X-Requested-With', 'XMLHttpRequest')

    if extraHeaders:
        for header, headerval in extraHeaders.iteritems():
            req.add_header(header, headerval)

    log.debug("Getting target '%s' (original: %s)" % (target, url))
    response = urllib2.urlopen(req, data)
    log.debug("Getting target '%s' (original: %s)" % (target, url))

    if cookieJar:
        cookieJar.save(cookies, ignore_discard=True)

    if returnResponse:
        return response

    html = response.read()
    response.close()

    if cleanup:
        html = cleanHtml(html)

    return html

def setupCookiesForRequest(cookiesFile):
    '''creates a cookie jar, loads the cookies from a file and sets up the urllib2 opener
    @param cookiesFile: the file with cookies to load
    @return: the cookie jar loaded'''
    import cookielib, os

    cookieJar = cookielib.LWPCookieJar()
    if os.path.isfile(cookiesFile):
        log.debug("loading cookies from file '%s'" % cookiesFile)
        cookieJar.load(cookiesFile)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    urllib2.install_opener(opener)

    log.debug("installed http cookie handler for cookie jar '%s'" % str(cookieJar))

    return cookieJar


def getTarget(url):
    target = url
    if url.find('http://') < 0:
        target = "http://www.primewire.ag" + url
    return target

def cleanHtml(html):
    '''Cleanup html by unescaping common html
    @param html: original HTML to be cleaned up'''
    clean = re.sub('&eacute;', 'ea', html)
    clean = re.sub('&amp;', '&', clean)
    clean = re.sub('&quot;', '', clean)
    clean = re.sub('&nbsp;<font class=".+?">.+?</font>', '', clean)
    clean = re.sub('&#x22;', '', clean)
    return clean
