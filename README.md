# PySmartCache


PySmartCache is a way to get automatic caching and caching invalidation for functions/methods.

Idea is simple: You just need to decorate the target function/method making explicit which signature infos are keys to this cache.

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

Seriouly. That's it. =P  
For more dense details please refer to [the docs](doc.md)
