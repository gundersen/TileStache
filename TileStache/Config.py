""" The configuration bits of TileStache.

TileStache configuration is stored in JSON files, and is composed of two main
top-level sections: "cache" and "layers". There are examples of both in this
minimal sample configuration:

    {
      "cache": {"name": "Test"},
      "layers": {
        "ex": {
            "provider": {"name": "mapnik", "mapfile": "style.xml"},
            "projection": "spherical mercator"
        } 
      }
    }

The contents of the "cache" section are described in greater detail in the
TileStache.Caches module documentation. Here is a different sample:

    "cache": {
      "name": "Disk",
      "path": "/tmp/stache",
      "umask": "0000"
    }

The "layers" section is a dictionary of layer names which are specified in the
URL of an individual tile. More detail on the configuration of individual layers
can be found in the TileStache.Core module documentation. Another sample:

    {
      "cache": ...,
      "layers": 
      {
        "example-name":
        {
            "provider": { ... },
            "metatile": { ... },
            "stale lock timeout": ...,
            "projection": ...
        }
      }
    }

In-depth explanations of the layer components can be found in the module
documentation for TileStache.Providers, TileStache.Core, and TileStache.Geography.
"""

from sys import stderr
from os.path import realpath, join as pathjoin

try:
    from json import dumps as json_dumps
except ImportError:
    from simplejson import dumps as json_dumps

import Core
import Caches
import Providers
import Geography

class Configuration:
    """ A complete site configuration, with a collection of Layer objects.
    """
    def __init__(self, cache, dirpath):
        self.cache = cache
        self.dirpath = dirpath
        self.layers = {}

def buildConfiguration(config_dict, dirpath='.'):
    """ Build a configuration dictionary into a Configuration object.
    
        The second argument is an optional dirpath that specifies where in the
        local filesystem the parsed dictionary originated, to make it possible
        to resolve relative paths.
    """
    cache_dict = config_dict.get('cache', {})
    cache = _parseConfigfileCache(cache_dict, dirpath)
    
    config = Configuration(cache, realpath(dirpath))
    
    for (name, layer_dict) in config_dict.get('layers', {}).items():
        config.layers[name] = _parseConfigfileLayer(layer_dict, config, dirpath)

    return config

def _parseConfigfileCache(cache_dict, dirpath):
    """ Used by parseConfigfile() to parse just the cache parts of a config.
    """
    if cache_dict.has_key('name'):
        _class = Caches.getCacheByName(cache_dict['name'])
        kwargs = {}
        
        if _class is Caches.Test:
            if cache_dict.get('verbose', False):
                kwargs['logfunc'] = lambda msg: stderr.write(msg + '\n')
    
        elif _class is Caches.Disk:
            kwargs['path'] = realpath(pathjoin(dirpath, cache_dict['path']))
            
            if cache_dict.has_key('umask'):
                kwargs['umask'] = int(cache_dict['umask'], 8)
    
        else:
            raise Exception('Unknown cache: %s' % cache_dict['name'])
        
    elif cache_dict.has_key('class'):
        _class = loadClassPath(cache_dict['class'])
        kwargs = cache_dict.get('kwargs', {})
        kwargs = dict( [(str(k), v) for (k, v) in kwargs.items()] )

    else:
        raise Exception('Missing required cache name or class: %s' % json_dumps(cache_dict))

    cache = _class(**kwargs)

    return cache

def _parseConfigfileLayer(layer_dict, config, dirpath):
    """ Used by parseConfigfile() to parse just the layer parts of a config.
    """
    projection = layer_dict.get('projection', 'spherical mercator')
    projection = Geography.getProjectionByName(projection)
    
    #
    # Add cache lock timeouts
    #
    
    layer_kwargs = {}
    
    if layer_dict.has_key('stale lock timeout'):
        layer_kwargs['stale_lock_timeout'] = int(layer_dict['stale lock timeout'])
    
    #
    # Do the metatile
    #

    meta_dict = layer_dict.get('metatile', {})
    metatile_kwargs = {}

    for k in ('buffer', 'rows', 'columns'):
        if meta_dict.has_key(k):
            metatile_kwargs[k] = int(meta_dict[k])
    
    metatile = Core.Metatile(**metatile_kwargs)
    
    #
    # Do the provider
    #

    provider_dict = layer_dict['provider']

    if provider_dict.has_key('name'):
        _class = Providers.getProviderByName(provider_dict['name'])
        provider_kwargs = {}
        
        if _class is Providers.Mapnik:
            mapfile = provider_dict['mapfile']
            provider_kwargs['mapfile'] = realpath(pathjoin(dirpath, mapfile))
        
        elif _class is Providers.Proxy:
            if provider_dict.has_key('url'):
                provider_kwargs['url'] = provider_dict['url']
            if provider_dict.has_key('provider'):
                provider_kwargs['provider_name'] = provider_dict['provider']
        
    elif provider_dict.has_key('class'):
        _class = loadClassPath(provider_dict['class'])
        provider_kwargs = provider_dict.get('kwargs', {})
        provider_kwargs = dict( [(str(k), v) for (k, v) in provider_kwargs.items()] )

    else:
        raise Exception('Missing required provider name or class: %s' % json_dumps(provider_dict))
    
    #
    # Finish him!
    #

    layer = Core.Layer(config, projection, metatile, **layer_kwargs)
    layer.provider = _class(layer, **provider_kwargs)
    
    return layer

def getTypeByExtension(extension):
    """ Get mime-type and PIL format by file extension.
    """
    if extension.lower() == 'png':
        return 'image/png', 'PNG'

    elif extension.lower() == 'jpg':
        return 'image/jpeg', 'JPEG'

    else:
        raise Core.KnownUnknown('Unknown extension: "%s"' % extension)

def loadClassPath(classpath):
    """ Load external class based on a path.
    
        Example classpath: "Module.Submodule.Classname",
    """
    classpath = classpath.split('.')
    module = __import__('.'.join(classpath[:-1]), fromlist=classpath[-1])
    _class = getattr(module, classpath[-1])
    
    return _class
