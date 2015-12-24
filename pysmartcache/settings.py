# -*- coding: utf-8 -*-


class PySmartCacheSettings(object):
    __slots__ = ['verbose', 'timeout', 'cache_backend', 'cache_host', ]

    verbose = None
    timeout = None
    cache_backend = None
    cache_host = None

    @classmethod
    def reset(cls):
        for attr in cls.__slots__:
            setattr(cls, attr, None)
