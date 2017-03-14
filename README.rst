PySmartCache
=============

PySmartCache is a way to get automatic caching and caching invalidation for functions/methods. It's working on both python2 and python3.

Idea is quite simple: you just need to decorate your function/method with :code:`@cache()`, and :code:`pysmartcache` will take care of the rest (caching based on arguments, cache invalidation, helpers for cache purge, cache refresh and cache invalidation, and so on).

For instance, change this:

.. code:: python

    def calculate_universe_mass(some_parameter, another_parameter, whatever):
        return 42


to this:

.. code:: python

    from pysmartcache import cache


    @cache()
    def calculate_universe_mass(some_parameter, another_parameter, whatever):
        return 42


Seriosuly. That's it. =P

For more dense details please refer to `the docs <https://github.com/filwaitman/pysmartcache/blob/master/doc.md>`_.


Contribute
----------

Did you think in some interesting feature, or have you found a bug? Please let me know!

Of course you can also download the project and send me some `pull requests <https://github.com/filwaitman/pysmartcache/pulls>`_. (see `contributing session <https://github.com/filwaitman/pysmartcache/blob/master/doc.md#contributing>`_ for more)


You can send your suggestions by `opening issues <https://github.com/filwaitman/pysmartcache/issues>`_.

You can contact me directly as well. Take a look at my contact information at `http://filwaitman.github.io/ <http://filwaitman.github.io/>`_ (email is preferred rather than mobile phone).
