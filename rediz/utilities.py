import json
import os
import numpy as np

def stem(name):
    return os.path.splitext(name)[0]

def get_json_safe(thing, getter):
    data = getter(thing)
    if has_nan(data):
        return None
    else:
        try:
            json.dumps(data)
            return shorten(data)
        except:
            return None


def has_nan(obj):
    if isinstance(obj, list):
        return any(map(has_nan, obj))
    elif isinstance(obj, dict):
        return has_nan(list(obj.values())) or has_nan(list(obj.keys()))
    else:
        try:
            return np.isnan(obj)
        except:
            return False


def shorten(obj,num=5):
    if isinstance(obj, list):
        return obj[:num]
    elif isinstance(obj, dict):
        return dict([(k, shorten(v)) for k, v in obj.items()])
    else:
        return obj