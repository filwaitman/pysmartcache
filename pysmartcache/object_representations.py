# -*- coding: utf-8 -*-

import abc
import datetime
from decimal import Decimal
import hashlib
import json

from pysmartcache.exceptions import UniqueRepresentationNotFound, InvalidTypeForUniqueRepresentation


class UniqueRepresentation(object, metaclass=abc.ABCMeta):
    @classmethod
    def all_subclasses(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in s.all_subclasses()]

    @classmethod
    def to(cls, obj):
        for subclass in cls.all_subclasses():
            unique_representation = subclass().get_unique_representation(obj)
            if unique_representation is not None:
                if not isinstance(unique_representation, str):
                    raise InvalidTypeForUniqueRepresentation(
                        '{} returned non-string unique representation for {} instance: {}'
                        .format(subclass, type(obj), unique_representation)
                    )
                return unique_representation
        raise UniqueRepresentationNotFound(
            'Object of type {} has not declared an unique representation'.format(type(obj))
        )

    @abc.abstractmethod
    def get_unique_representation(self, obj):
        pass


def get_unique_representation(obj):
    if hasattr(obj, '__cache_key__'):
        result = obj.__cache_key__()
        if not isinstance(result, str):
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
            return UniqueRepresentation.to(obj)

    elif isinstance(obj, dict):
        result = []
        for key, value in list(obj.items()):
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
