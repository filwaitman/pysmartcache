# -*- coding: utf-8 -*-
import datetime
import functools
import hashlib
import inspect
import os

import pylibmc


def cache_engine_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs):
    return CacheEngine(func, keys, function_args, function_kwargs, timeout=timeout, hosts=hosts, verbose=verbose)


def cache_invalidate_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs):
    return cache_engine_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs).invalidate()


def cache_refresh_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs):
    return cache_engine_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs).refresh()


def cache_info_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs):
    return cache_engine_for(func, keys, timeout, hosts, verbose, *function_args, **function_kwargs).info()


def depth_getattr(current_object, key):
    if not key:
        return current_object

    parts = key.split('.')
    str_attr = '.'.join(parts[1:])
    return depth_getattr(getattr(current_object, parts[0]), str_attr)


def get_unique_representation(obj):
    if hasattr(obj, '__cache_key__'):
        result = obj.__cache_key__()
    elif hasattr(obj, 'uuid'):
        result = obj.uuid
    elif hasattr(obj, 'id'):
        result = obj.id
    elif isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        result = obj.isoformat()
    elif not hasattr(obj, '__iter__'):
        result = obj
    elif isinstance(obj, dict):
        result = []
        for key, value in obj.items():
            result.append(get_unique_representation(key))
            result.append(get_unique_representation(value))
        result = '--'.join(result)
    else:
        result = []
        for sub_object in obj:
            result.append(get_unique_representation(sub_object))
        result = '--'.join(result)

    result = repr(result)

    if len(result) > 150:
        result = hashlib.md5(result).hexdigest()

    return result


class CacheClient(object):
    ''' This class is isolated in order to avoid creating many connections to memcached '''
    @classmethod
    def get(cls, hosts):
        if not hasattr(cls, '_client') or not hasattr(cls, '_client_hosts') or cls._client_hosts != hosts:
            cls._client_hosts = hosts
            cls._client = pylibmc.Client(hosts)
        return cls._client


class CacheEngine(object):
    DEFAULT_TIMEOUT = 3600
    DEFAULT_HOSTS = ['127.0.0.1:11211', ]
    DEFAULT_VERBOSE = False

    def __init__(self, func, keys, function_args, function_kwargs, timeout=None, hosts=None, verbose=False):
        self.timeout = self.__class__._get_timeout(timeout)
        self.hosts = self.__class__._get_hosts(hosts)
        self.verbose = self.__class__._get_verbose(verbose)

        self.func = func
        self.keys = keys
        self.function_args = function_args
        self.function_kwargs = function_kwargs

        self.function_arguments = inspect.getcallargs(self.func, *self.function_args, **self.function_kwargs)
        self.now_reference = datetime.datetime.now()
        self.cache_client = self.__class__.client(self.hosts)

        self._create_func_full_qualified_name()
        self._create_cache_key()

        self.stored_info = self.info()
        self.stored_value = self.stored_info['value'] if self.stored_info else None
        self.stored_at = self.stored_info['date added'] if self.stored_info else None

        if self.verbose:
            print '-' * 50
            print 'KEY: {}'.format(self.cache_key)

    @classmethod
    def _get_timeout(cls, timeout):
        if timeout is None:
            timeout = os.environ.get('PYSMARTCACHE_TIMEOUT')
            if timeout:
                try:
                    timeout = int(timeout)
                except:
                    raise RuntimeError('PYSMARTCACHE_TIMEOUT OS var must be numeric')

        if timeout is None:
            timeout = cls.DEFAULT_TIMEOUT

        if timeout <= 0:
            raise RuntimeError('Timeout must be positive')

        return timeout

    @classmethod
    def _get_hosts(cls, hosts):
        if hosts is None:
            hosts = os.environ.get('PYSMARTCACHE_HOSTS')
            if hosts:
                hosts = hosts.split(',')

        if hosts is None:
            hosts = cls.DEFAULT_HOSTS

        if not hosts:
            raise RuntimeError('Hosts can not be empty')

        return hosts

    @classmethod
    def _get_verbose(cls, verbose):
        if verbose is None:
            verbose = os.environ.get('PYSMARTCACHE_VERBOSE')
            if verbose:
                try:
                    verbose = int(verbose)
                except:
                    raise RuntimeError('PYSMARTCACHE_VERBOSE OS var must be numeric')
                if verbose not in (0, 1):
                    raise RuntimeError('PYSMARTCACHE_VERBOSE OS var must be 0 or 1')

        if verbose is None:
            verbose = cls.DEFAULT_VERBOSE
        return verbose

    @classmethod
    def _cache_outdated_signal(cls):
        pass  # this method is here just for testing purposes.

    @classmethod
    def _cache_miss_signal(cls):
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

    @classmethod
    def client(cls, hosts=None):
        hosts = cls._get_hosts(hosts)
        return CacheClient.get(hosts)

    @classmethod
    def purge(cls, hosts=None):
        hosts = cls._get_hosts(hosts)
        return cls.client(hosts=hosts).flush_all()

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
            return self.cache_miss()

    def reset_cache(self):
        result = self.func(*self.function_args, **self.function_kwargs)
        self.cache_client.set(self.cache_key, [result, self.now_reference])
        return result

    def cache_outdated(self):
        self.__class__._cache_outdated_signal()
        return self.reset_cache()

    def cache_miss(self):
        self.__class__._cache_miss_signal()
        return self.reset_cache()

    def cache_hit(self):
        self.__class__._cache_hit_signal()
        return self.stored_value


def cache(keys, timeout=None, hosts=None, verbose=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*function_args, **function_kwargs):
            engine = CacheEngine(func, keys, function_args, function_kwargs, timeout=timeout, hosts=hosts, verbose=verbose)
            return engine.execute()

        wrapper.cache_engine_for = functools.partial(cache_engine_for, func, keys, timeout, hosts, verbose)
        wrapper.cache_invalidate_for = functools.partial(cache_invalidate_for, func, keys, timeout, hosts, verbose)
        wrapper.cache_info_for = functools.partial(cache_info_for, func, keys, timeout, hosts, verbose)
        wrapper.cache_refresh_for = functools.partial(cache_refresh_for, func, keys, timeout, hosts, verbose)

        wrapper.is_cache_decorated = True
        wrapper.cache_keys = keys

        return wrapper

    return decorator
