# Table of contents:

1. [Intro](#intro)
    1. [Installation](#installation)
    2. [Simplest case](#simplest-case)
    3. [Keys inclusion/exclusion](#keys-inclusionexclusion)
    4. [Defining keys in-depth](#defining-keys-in-depth)
    5. [Using callables as keys](#using-callables-as-keys)
2. [Cache helpers](#cache-helpers)
    1. [Refresh cache](#refresh-cache)
3. [Settings](#settings)
    1. [Cache client](#cache-client)
    2. [Cache Time to live / timeout](#cache-time-to-live--timeout)
    3. [Caching exceptions behavior](#caching-exceptions-behavior)
    4. [Disable PySmartCache](#disable-pysmartcache)
    5. [Cache host](#cache-host)
4. [Advanced usage](#advanced-usage)
    1. [Defining your own clients](#defining-your-own-clients)
5. [Contributing](#contributing)
    1. [Preparing environment](#preparing-environment)
    2. [Rules to contribute](#rules-to-contribute)



## Intro


### Installation
This lib can use as backend [memcached](http://memcached.org/), [redis](http://redis.io/) or [django itself](https://www.djangoproject.com/). Please install/configure the one you want to use first.     
After this:
* Set the env var `PYSMARTCACHE_CLIENT` to be one of `memcached`, `redis` or `django`;
* `pip install pysmartcache`.


### Simplest case
Let's suppose you have a heavy function and you want to cache it. Of course you can deal with cache manually... or, you can just use the `@cache()` decorator.   
`@cache()` by default will cache this function according to its parameters - just like the `memoizer` design pattern. So the simplest usage case is:
```python
from pysmartcache import cache


@cache()
def calculate_universe_mass(some_parameter, another_parameter, whatever):
    return 42
```


### Keys inclusion/exclusion
Now let's suppose you have a heavy function that receives a parameter such `verbose=True`. Well, (hopefully) this parameter will not change the result of function execution itself, so `@cache()` should ignore it.  
For this to work you can use `keys` parameter:  
```python
from pysmartcache import cache


@cache(keys=['some_parameter', 'another_parameter', 'whatever'])
def calculate_universe_mass(some_parameter, another_parameter, whatever, verbose=True):
    return 42
```


### Defining keys in-depth
Sometimes you are trying to cache a method which `self` is not such a good key for cache itself.  
Let's suppose you have a class `Statistics`, related to an `Investor`, which has an identifier `uuid` attribute. Using `@cache()` as-is will try to cache based on `self`, when we wanted to cache based on `self.investor.uuid`. Voila:
```python
from pysmartcache import cache


class Investor(object):
    def __init__(self, uuid):
        self.uuid = uuid


class Statistics(object):
    def __init__(self, investor, debug):
        self.investor = investor
        self.debug = debug  # This is not useful for key caching.
        
    @cache(keys=['self.investor.uuid', ])
    def get_internal_return_rate(self):
        return 42
```


### Using callables as keys
You can use callables on `keys` parameter inside `@cache`. Just use the magic `__call__` key. Check it out:
```python
from pysmartcache import cache


class Place(object):
    def __init__(self, lat, lng, name, whatever):
        self.lat = lat
        self.lng = lng
        self.name = name
        self.whatever = whatever

    def get_coordinates(self):
        return (self.lat, self.lng)

    @cache(keys=['self.get_coordinates.__call__', ])
    def fetch_address_data_on_gmaps_api():
        return 42
```



## Cache helpers


### Refresh cache
Refreshing a cache will force cached function's re-execution and update its time to live:
```python
import time

from pysmartcache import cache


@cache()
def its_a_sum(a, b):
    return a + b


assert its_a_sum(2, 4) == 6

assert its_a_sum(2, 4, _cache_refresh=True) == 6  # Now forcing function execution again
```



## Settings


### Cache client
This setting is the only one required. For now `Django`, `memcached` and `redis` are supported. Use the env var `PYSMARTCACHE_CLIENT` to set it.


### Cache Time to live / timeout
Default cache time to live / timeout is `3600` seconds (a.k.a. 1 hour). You can change it by:
- Using `ttl` parameter on `@cache()` call;
- Defining an env var called `PYSMARTCACHE_DEFAULT_TTL`.  


### Caching exceptions behavior
By default, PySmartCache will not cache the "result" of an execution if an exception occurs. You can change it by:
- Setting `cache_exception` parameter on `@cache()` call to `True`;
- Defining an env var called `PYSMARTCACHE_DEFAULT_CACHE_EXCEPTION` and setting it to `'True'`.  

You can also define a custom TTL for exceptions cached by:
- Setting `cache_exception_ttl` parameter on `@cache()` call;
- Defining an env var called `PYSMARTCACHE_DEFAULT_CACHE_EXCEPTION_TTL`.  


### Disable PySmartCache
If you want to disable PySmartCache execution you don't need to remove the `@cache` call. Instead, you can just disable it (globally or per callable). You can do this by:
- Setting `enabled` parameter on `@cache()` call to `False`;
- Defining an env var called `PYSMARTCACHE_DEFAULT_ENABLED` and setting it to `'False'`.  


### Cache host
This setting is required for `memcached`/`redis` clients. Use the env var `PYSMARTCACHE_HOST` to set it.



## Advanced usage


### Defining your own clients
`PySmartCache` comes with `django`, `memcached` and `redis` clients implemented. You can implement and use another ones.  
All you have to do is create a `class` for this new client, inheriting from `CacheClient` and define a minimal set of methods.  
Take a look at this example:
```python
from pysmartcache import CacheClient, PySmartCacheSettings


class MyCustomClient(CacheClient):
    name = 'custom'  # This is the client's name for lookup. Use something like 'memcached', 'redis', 'rds', 'mongodb', etc.

    def get(self, key):
        pass

    def set(self, key, value, ttl):
        pass  # I strongly suggest you to always set values as a pickle str (it avoids problems with data types, trust me)
```



## Contributing
If you like the project and feel that you can contribute for it, feel free!  =]  
I'll be glad and will add your name to the project's authors.


### Preparing environment
Firstly, make sure to install both memcached and redis.  
In order to prepare your environment to development:
```bash
# git clone ...
python setup.py install
pip install -r requirements_test.txt
make test
```


### Rules to contribute
* Follow the [PEP8](https://www.python.org/dev/peps/pep-0008/).
  * Use 120 characters as line length.
* Readability is more important than performance.
  * If you have to decide between an ugly golden solution and a clean 10% slower one, use the latter.
* Don't abbrv d cod!
  * Never abbreviate the code. Variable names, test cases, class names, method names... please, be verbose.
* Write tests.
