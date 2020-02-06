import re, sys, json
import numpy as np
import threezaconventions.crypto
from redis.client import list_or_args
from typing import List, Union, Any, Optional

KeyList   = List[Optional[str]]
NameList  = List[Optional[str]]
Value     = Union[str,int]
ValueList = List[Optional[Value]]
DelayList = List[Optional[int]]

class RedizConventions(object):

    def __init__(self):
        pass

    @staticmethod
    def sep():
        return "::"

    @staticmethod
    def assert_not_in_reserved_namespace(names, *args):
        names = list_or_args(names, args)
        if any(RedizConventions.sep() in name for name in names):
            raise Exception("Operation attempted with a name that uses " + RedizConventions.sep())

    @staticmethod
    def min_key_len():
        return 18

    @staticmethod
    def is_valid_name(name: str):
        name_regex = re.compile(r'^[-a-zA-Z0-9_.:]{1,200}\.[json,HTML]+$', re.IGNORECASE)
        return (re.match(name_regex, name) is not None) and (not RedizConventions.sep() in name)

    @staticmethod
    def is_valid_value(value):
        return isinstance(value, (str, int, float)) and sys.getsizeof(value) < 100000

    @staticmethod
    def is_small_value(value):
        """ A vector of 100 floats is considered small, for example """
        return isinstance(value, (str, int, float)) and sys.getsizeof(value) < 1000

    @staticmethod
    def is_scalar_value(value):
        try:
            fv = float(value)
            return True
        except:
            return False

    @staticmethod
    def is_vector_value(value):
        if isinstance(value, (list, tuple)):
            return True
        else:
            try:
                v = json.loads(value)
                return RedizConventions.is_vector_value(value)
            except:
                return False

    @staticmethod
    def is_dict_value(value):
        try:
            d = dict(value)
            return True
        except:
            try:
                v = json.loads(value)
                return RedizConventions.is_dict_value(value)
            except:
                return False

    @staticmethod
    def is_vector_value(value):
        try:
            fv = json.loads(value)
            return True
        except:
            return False

    @staticmethod
    def to_record(value):
        if RedizConventions.is_scalar_value(value):
            fields = {"0": value}
        elif RedizConventions.is_dict_value(value):
            fields = dict(value)
        elif RedizConventions.is_vector_value(value):
            fields = dict(enumerate(list(value)))
        else:
            fields = {"value": value}
        return fields

    @staticmethod
    def to_float(values):
        # Canonical way to convert str or [str] or [[str]] to float equivalent with nan replacing None
        return np.array(values, dtype=np.float32).tolist()

    @staticmethod
    def is_valid_key(key):
        return isinstance(key, str) and len(key) > RedizConventions.min_key_len()

    @staticmethod
    def random_key():
        return threezaconventions.crypto.random_key()

    @staticmethod
    def random_name():
        return threezaconventions.crypto.random_key() + '.json'

    @staticmethod
    def hash(s):
        return threezaconventions.crypto.hash5(s)