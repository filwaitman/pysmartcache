# PySmartCache


## TL;DR
PySmartCache is a way to get automatic caching and caching invalidation for functions/methods.

Idea is simple: You just need to decorate the target function/method making explicit which signature infos are keys to this cache.

For instance, change this:
```python
def calculate_rate_for(date_reference, verbose=True):
    pass
```
to this:
```python
from pysmartcache import cache


@cache(['date_reference', ])
def calculate_rate_for(date_reference, verbose=True):
    pass
```

You can also refer to arguments in-depth. For instance:
```python
from pysmartcache import cache


class Calculator(object):
    def __init__(self, rate):
        self.rate = rate


class IRR(object):
    def __init__(self, calculator):
        self.calculator = calculator


    @cache(['self.calculator.rate', 'date'])
    def get_value(self, date):
        pass
```

Learn by doing:
```python
import time

from pysmartcache import cache

@cache(['a', 'b'], verbose=True, timeout=10)
def not_so_efficient_sum(a, b):
    print 'calculating...'
    time.sleep(5)
    return a + b


result = not_so_efficient_sum(2, 2)
# KEY: __main__.not_so_efficient_sum//2//2
# MISSED
# calculating...

print result
# 4

time.sleep(1)
result = not_so_efficient_sum(2, 2)
# KEY: __main__.not_so_efficient_sum//2//2
# HIT (added to cache 1.01 seconds ago)

print result
# 4

not_so_efficient_sum.cache_info_for(2, 2)  # see info stored about this cached item, if available. Returns None if item not cached
# {
#     'age': 6.15,
#     'date added': datetime.datetime(2015, 1, 1, 1, 1, 1, 1),
#     'outdated': False,
#     'timeout': 10,
#     'value': 4
# }

time.sleep(5)
result = not_so_efficient_sum.cache_refresh_for(2, 2)  # recalculate cached info, even if it is now expired. Update 'date added' for this item
# KEY: __main__.not_so_efficient_sum//2//2
# REFRESHING
# calculating...

print result
# 4

not_so_efficient_sum.cache_info_for(2, 2)
# {
#     'age': 5.01,  # just updated
#     'date added': datetime.datetime(2015, 1, 1, 1, 1, 6, 1),
#     'outdated': False,
#     'timeout': 10,
#     'value': 4
# }


not_so_efficient_sum.cache_invalidate_for(2, 2)  # remove this item from cache
# KEY: __main__.not_so_efficient_sum//2//2
# INVALIDATING

not_so_efficient_sum.cache_info_for(2, 2)
# None
```

## Installation
This lib uses [memcached](http://memcached.org/). Please install it before trying to install this.
When you have installed memcached, you just need to run `pip install pysmartcache`.


## Extra settings
Some lib settings can be changed via decorator parameters and OS vars. See below. Note that when both decorator parameter and OS var are present, decorator parameter is the one being considered.

| attribute name           | decorator parameter name | OS var name              | default value            |
| -------------------------|--------------------------|--------------------------|--------------------------|
| timeout                  | timeout                  | PYSMARTCACHE_TIMEOUT     | 3600                     |
| verbose                  | verbose                  | PYSMARTCACHE_VERBOSE     | False                    |
| hosts                    | hosts                    | PYSMARTCACHE_HOSTS       | ['127.0.0.1:11211', ]    |
