# -*- coding: utf-8 -*-



def depth_getattr(current_object, key):
    if not key:
        return current_object

    parts = key.split('.')
    str_attr = '.'.join(parts[1:])
    return depth_getattr(getattr(current_object, parts[0]), str_attr)
