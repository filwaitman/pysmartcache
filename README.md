# PySmartCache


PySmartCache is a way to get automatic caching and caching invalidation for functions/methods.

Idea is quite simple: you just need to decorate your function/method, and `pysmartcache` will take care of the rest (caching based on arguments, cache invalidation, helpers for cache purge, cache refresh and cache invalidation, and so on).

For instance, change this:
```python
def calculate_universe_mass(some_parameter, another_parameter, whatever):
    return 42
```
to this:
```python
from pysmartcache import cache


@cache()
def calculate_universe_mass(some_parameter, another_parameter, whatever):
    return 42
```

Seriosuly. That's it. =P  
For more dense details please refer to [the docs](doc.md)
