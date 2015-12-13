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


## Installation
This lib uses [memcached](http://memcached.org/). Please install it before trying to install this.
When you have installed memcached, you just need to run `pip install pysmartcache  # TODO`.


## Extra settings
Some lib settings can be changed via decorator parameters and OS vars. See below. Note that when both decorator parameter and OS var are present, decorator parameter is the one being considered.

| attribute name           | decorator parameter name | OS var name              | default value            |
| -------------------------|--------------------------|--------------------------|--------------------------|
| timeout                  | timeout                  | PYSMARTCACHE_TIMEOUT     | 3600                     |
| verbose                  | verbose                  | PYSMARTCACHE_VERBOSE     | False                    |
| hosts                    | hosts                    | PYSMARTCACHE_HOSTS       | ['127.0.0.1:11211', ]    |
