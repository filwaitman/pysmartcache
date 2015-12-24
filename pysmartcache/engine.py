# -*- coding: utf-8 -*-
import datetime
import functools
import inspect

from pysmartcache.clients import CacheClient
from pysmartcache.exceptions import ImproperlyConfigured
from pysmartcache.object_representations import get_unique_representation
from pysmartcache.settings import PySmartCacheSettings
from pysmartcache.utils import depth_getattr


def _cache_engine_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs):
    return CacheEngine(func, keys, function_args, function_kwargs, timeout=timeout,
                       cache_backend=cache_backend, cache_host=cache_host, verbose=verbose)


def cache_invalidate_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs):
    return _cache_engine_for(func, keys, timeout, cache_backend, cache_host, verbose,
                             *function_args, **function_kwargs).invalidate()


def cache_refresh_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs):
    return _cache_engine_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs).refresh()


def cache_info_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs):
    return _cache_engine_for(func, keys, timeout, cache_backend, cache_host, verbose, *function_args, **function_kwargs).info()


class CacheEngine(object):
    def __init__(self, func, keys, function_args, function_kwargs,
                 timeout=None, cache_backend=None, cache_host=None, verbose=None):
        self.timeout = PySmartCacheSettings._get_timeout(timeout)
        self.cache_backend = PySmartCacheSettings._get_cache_backend(cache_backend)
        self.verbose = PySmartCacheSettings._get_verbose(verbose)

        self.func = func
        self.keys = keys
        self.function_args = function_args
        self.function_kwargs = function_kwargs

        self.function_arguments = inspect.getcallargs(self.func, *self.function_args, **self.function_kwargs)
        self.now_reference = datetime.datetime.now()
        self.cache_client = CacheClient.instantiate(self.cache_backend, cache_host)

        self._create_func_full_qualified_name()
        self._create_cache_key()

        self.stored_info = self.info()
        self.stored_value = self.stored_info['value'] if self.stored_info else None
        self.stored_at = self.stored_info['date added'] if self.stored_info else None

        if self.verbose:
            print '-' * 50
            print 'KEY: {}'.format(self.cache_key)

    @classmethod
    def _cache_outdated_signal(cls):
        pass  # this method is here just for testing purposes.

    @classmethod
    def _cache_missed_signal(cls):
        pass  # this method is here just for testing purposes.

    @classmethod
    def _cache_hit_signal(cls):
        pass  # this method is here just for testing purposes.

    def _create_func_full_qualified_name(self):
        self.func_full_qualified_name = [self.func.__module__, self.func.__name__]
        if 'self' in self.function_arguments:
            self.func_full_qualified_name.insert(1, self.function_arguments['self'].__class__.__name__)
        self.func_full_qualified_name = '.'.join(self.func_full_qualified_name)
        if len(self.func_full_qualified_name) > 100:
            self.func_full_qualified_name = self.func_full_qualified_name[:45] + '...' + self.func_full_qualified_name[-45:]

    def _create_cache_key(self):
        sanitized_keys = [self.func_full_qualified_name]
        for key in self.keys:
            parts = key.split('.')
            current_object = self.function_arguments[parts[0]]
            str_attr = '.'.join(parts[1:])

            target_object = depth_getattr(current_object, str_attr)
            sanitized_keys.append(get_unique_representation(target_object))

        self.cache_key = '//'.join(sanitized_keys)

    def invalidate(self):
        if self.verbose:
            print 'INVALIDATING'
        self.cache_client.delete(self.cache_key)

    def refresh(self):
        if self.verbose:
            print 'REFRESHING'
        return self.reset_cache()

    def info(self):
        result = self.cache_client.get(self.cache_key)
        if result:
            age = (self.now_reference - result[1]).total_seconds()
            return {
                'value': result[0],
                'date added': result[1],
                'outdated': age >= self.timeout,
                'timeout': self.timeout,
                'age': age,
            }

    def execute(self):
        if self.stored_info:
            if self.stored_info['outdated']:
                if self.verbose:
                    print 'OUTDATED (added to cache {:.2f} seconds ago)'.format(self.stored_info['age'])
                return self.cache_outdated()

            else:
                if self.verbose:
                    print 'HIT (added to cache {:.2f} seconds ago)'.format(self.stored_info['age'])
                return self.cache_hit()

        else:
            if self.verbose:
                print 'MISSED'
            return self.cache_missed()

    def reset_cache(self):
        result = self.func(*self.function_args, **self.function_kwargs)
        self.cache_client.set(self.cache_key, [result, self.now_reference])
        return result

    def cache_outdated(self):
        self.__class__._cache_outdated_signal()
        return self.reset_cache()

    def cache_missed(self):
        self.__class__._cache_missed_signal()
        return self.reset_cache()

    def cache_hit(self):
        self.__class__._cache_hit_signal()
        return self.stored_value


def cache(include=None, exclude=None, timeout=None, cache_backend=None, cache_host=None, verbose=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*function_args, **function_kwargs):
            engine = CacheEngine(func, keys, function_args, function_kwargs, timeout=timeout,
                                 cache_backend=cache_backend, cache_host=cache_host, verbose=verbose)
            return engine.execute()

        all_keys = inspect.getargspec(func).args
        if include and exclude:
            raise ImproperlyConfigured('You shall not provide both include and exclude arguments')
        elif not include and not exclude:
            keys = all_keys
        elif include:
            keys = include
        elif exclude:
            for exclude_key in exclude:
                if exclude_key not in all_keys:
                    raise ImproperlyConfigured('Invalid key on exclude: "{}". Keys allowed to be excluded: "{}"'
                                               .format(exclude_key, '", "'.join(all_keys)))
            keys = [item for item in all_keys if item not in exclude]

        wrapper.cache_invalidate_for = functools.partial(cache_invalidate_for, func, keys, timeout,
                                                         cache_backend, cache_host, verbose)
        wrapper.cache_info_for = functools.partial(cache_info_for, func, keys, timeout, cache_backend, cache_host, verbose)
        wrapper.cache_refresh_for = functools.partial(cache_refresh_for, func, keys, timeout, cache_backend, cache_host, verbose)

        wrapper.is_cache_decorated = True
        wrapper.cache_keys = keys
        wrapper.cache_keys_included = include or []
        wrapper.cache_keys_excluded = exclude or []

        return wrapper

    return decorator
