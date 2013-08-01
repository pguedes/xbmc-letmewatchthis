'''
A module to support creating plugin facades for XBMC in a simplified programming environment.

This module allows the plugin to be programmed has a set of handler functions that are registered
via the decorators on this module. When a request comes in from XBMC, plugin.handle() can collect
the parameters, map them to the correct handler function arguments, invoke it and use the results 
to either play or show a listing in XBMC's GUI.

Handler functions must return a PluginResult which is a container for a list of results, with a
size (for progress indication) and a iterable of PluginMovieItem instances(or generator function)

A PluginMovieItem has a label a plugin mode and a map of arguments to use to invoke the 
corresponding handler function with.

Created on Aug 7, 2010

@author: pedro
'''
import inspect, logging
import xbmcgui
from metahandler.metahandlers import MetaData
from utils import pluginsupport

log = logging.getLogger("plugin")
metadataFacade = MetaData()


class PluginResult:
    def __init__(self, size, items):
        self.size = size
        self.items = items


class PluginMovieItem:
    """An item resolved by a plugin.
  Can be a link to a list of items or a playable item."""
    __listItem = None

    def __init__(self, name, url, mode=None, extraArgs=None, season=None, episode=None):
        """Create an item
    @param name: the label for this item
    @param url: the url to load this item
    @param mode: the mode for this link """
        self.label = name
        self.url = url
        self.mode = mode or "ROOT"
        self.imdbid = None
        self.extraArgs = extraArgs
        self.season = season
        self.episode = episode

    def getMetadataLabels(self):
        """returns the metadata labels to use in XBMC's GUI"""
        return {"title": self.label}

    def isPlayable(self):
        return modeHandlers[self.mode].playable

    def getLabel(self):
        return self.label

    def getLabels(self):
        return {'title': self.label}

    def getMetadataMediaType(self, xbmc_content_type):
        """
        Convert XBMC's content type to mediahandler's 'media type' thingy
        @return: searchable media type
        """
        translation = {"tvshows": "tvshow", "movies": "movie", "episodes": "episode"}
        print "xbmc content type is %s" % xbmc_content_type
        if xbmc_content_type in translation:
            print "translation is %s" % translation[xbmc_content_type]
            return translation[xbmc_content_type]

    def getPath(self):
        return self.url

    def buildContextMenu(self):
        pass

    def getListItem(self):
        """Create a list item for XBMC for this PluginMovieItem
    @return the list item for XBMC"""
        if self.__listItem:
            return self.__listItem

        # get the current mode from the plugin's invocation arguments
        args = pluginsupport.getArguments()
        print args

        contentTypeOfCurrentList = None
        if args:
            contentTypeOfCurrentList = modeHandlers[args["mode"]].getContentType()

        if not contentTypeOfCurrentList in ["tvshows", "movies", "episodes"]:
            metadata = self.getMetadataLabels()
        elif contentTypeOfCurrentList == 'episodes':
            metadata = metadataFacade.get_episode_meta(args['name'], args['imdbid'], self.season, self.episode)
        else:
            # get metadata for this item
            metadata = metadataFacade.get_meta(self.getMetadataMediaType(contentTypeOfCurrentList), self.getLabel())

        if 'cover_url' in metadata:
            thumb = metadata['cover_url']
        else:
            thumb = ""

        if 'imdb_id' in metadata:
            self.imdbid = metadata['imdb_id']

        self.__listItem = xbmcgui.ListItem(self.getLabel(), iconImage=thumb, thumbnailImage=thumb, path=self.getPath())
        self.__listItem.setInfo(type="Video", infoLabels=metadata)

        if 'backdrop_url' in metadata:
            fanart = metadata['backdrop_url']
            self.__listItem.setProperty('fanart_image', fanart)

        if self.isPlayable():
            self.__listItem.setProperty('IsPlayable', 'true')

        contextMenu = self.buildContextMenu()
        if contextMenu:
            self.__listItem.addContextMenuItems(contextMenu)

        return self.__listItem

    def getTargetUrl(self, action=None, extra=None):
        """Returns the url for this item to use by XBMC
    @param action: optional action to add to the url"""

        #
        # this needs to be removed... ugly hack to force calling getListItem() before this is called
        # as getListItem() will change the state of this object by setting the imdbid
        # this should be refactored out...
        #
        if not self.__listItem:
            self.getListItem()

        extra = extra or self.extraArgs
        if self.mode:
            argsMap = {"url": self.url, "mode": str(self.mode), "label": self.label, "name": self.label}
            if action:
                argsMap['action'] = action
            if extra:
                for key, value in extra.iteritems():
                    argsMap[key] = value
            if self.imdbid:
                argsMap['imdbid'] = self.imdbid
            return pluginsupport.encode(argsMap)
        return self.url


"""A registry of mode handlers"""
modeHandlers = {}
actionHandlers = {}
normalFlowActions = []


def mode(modeId, contentType=None, playable=False):
    """Decorator to register mode handler functions
  @param modeId: the mode to register the function for
  @param contentType: the content type this handler's generates
  @param playable: if the content is playable"""

    def decorate(function):
        log.debug("registering mode %r with content %r" % (modeId, contentType))
        modeHandlers[modeId] = HandlerWrapper(function, contentType, playable)

    return decorate


def root():
    """Decorator to register the root handler functions"""

    def decorate(function):
        log.debug("registering root")
        modeHandlers['ROOT'] = HandlerWrapper(function)

    return decorate


def action(actionId, normalFlow=False):
    """Decorator to register action handler functions
  @param actionId: the action to register the function for
  @param normalFlow: if this action should run like a normal flow action"""

    def decorate(function):
        actionHandlers[actionId] = HandlerWrapper(function)
        if normalFlow == True:
            normalFlowActions.append(actionId)

    return decorate


def __isAction(arguments):
    """Checks if a request is an action request
  @param arguments: the invocation arguments from XBMC
  @return true if this is an action request, false otherwise"""
    return arguments.has_key('action') and arguments['action'] not in normalFlowActions


def handle():
    """
  Handle an XBMC plugin request.
  This will get the appropriate handler function, execute it to get a PluginResult
  then if they-re in normal flor, handle the result by either listing the items or playing them.
  """
    arguments = pluginsupport.getArguments()

    def __getArgument(arg):
        if not arguments.has_key(arg):
            return None
        val = arguments[arg]
        del arguments[arg]
        return val

    if __isAction(arguments):
        action = __getArgument('action')
        log.debug("invoking action '%s'" % action)
        actionHandlers[action].call(arguments)
    else:
        mode = __getArgument('mode') or "ROOT"
        handler = modeHandlers[mode]
        log.debug("invoking mode %r handler with arguments %r" % (mode, arguments))
        result = handler.call(arguments)
        log.debug("results from mode %r handler: %r" % (mode, result))
        if handler.playable:
            log.debug("playing results for mode %r" % mode)
            pluginsupport.play(result.items)
        else:
            log.debug("listing results for mode %r" % mode)
            pluginsupport.list(result, handler.getContentType(arguments))
        pluginsupport.done()


class HandlerWrapper:
    """A wrapper for handler functions that can map arguments from XBMC's request
  to the handler functions parameters"""

    def __init__(self, handler, contentType=None, playable=False):
        """Creates a new wrapper for a handler function
    @param handler: the function to wrap
    @param contentType: the content type this handler generates
    @param playable: if the content is playable"""
        self.handlerFunction = handler
        self.contentType = contentType
        self.playable = playable

    def call(self, params={}):
        """Invokes the handler function
    @param params: the invocation params from XBMC
    @return: the result of the invocation of the handler function"""
        return _executeOne(self.handlerFunction, params)

    def getContentType(self, params=None):
        """Gets the content type for this handler
    @param params: the invocation params
    @return: the content type of this handler"""
        contentType = self.contentType
        params = params or pluginsupport.getArguments()
        if callable(contentType):
            contentType = contentType(params)
        return contentType


def __mapArgs(functionArgs, pluginParams):
    """Map the plugins invocation arguments to the handler function arguments
  The arguments are matched by label
  @param functionArgs: The list of arguments the function requires
  @param pluginParams: the available params from the invocation of the plugin (url)
  @return: a dict of arguments to invoke the handler function with"""
    args = {}
    for arg in functionArgs:
        if pluginParams.has_key(arg):
            args[arg] = pluginParams[arg]
    return args


def _executeOne(f, params={}):
    """Execute a function with some params from the plugin
  This method maps the url encoded params into the mode handler function's arguments 
  and then invokes the handler function
  @param params the request params"""
    fargs = inspect.getargspec(f)[0]
    if not fargs:
        return f()
    log.debug("Function has args: %s" % str(fargs))
    args = __mapArgs(fargs, params)
    log.debug("Dispatching call to function with args: %s" % str(args))
    return f(**args)

