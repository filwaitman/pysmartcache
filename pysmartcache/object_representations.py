# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import hashlib
import json

from pysmartcache.exceptions import UniqueRepresentationNotFound, InvalidTypeForUniqueRepresentation


def get_unique_representation(obj):
    if hasattr(obj, '__cache_key__'):
        result = obj.__cache_key__()
        if not isinstance(result, basestring):
            raise InvalidTypeForUniqueRepresentation('obj.__cache_key__() must return a string')
        result = '.'.join([obj.__module__, obj.__class__.__name__, result])

    elif hasattr(obj, 'uuid'):
        result = '.'.join([obj.__module__, obj.__class__.__name__, str(obj.uuid)])

    elif hasattr(obj, 'id'):
        result = '.'.join([obj.__module__, obj.__class__.__name__, str(obj.id)])

    elif isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        result = obj.isoformat()

    elif isinstance(obj, Decimal):
        result = str(float(obj))

    elif not hasattr(obj, '__iter__'):
        try:
            json.dumps(obj)
            result = repr(obj)
        except TypeError:
            raise UniqueRepresentationNotFound('Object of type {} has not declared an unique representation'.format(type(obj)))

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

    if len(result) > 150:
        result = hashlib.md5(result).hexdigest()

    return result
