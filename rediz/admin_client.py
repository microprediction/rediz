import fakeredis, sys, math, json, redis, time, random, itertools, datetime
import numpy as np
from collections import Counter, OrderedDict
from typing import List, Union, Any, Optional
from redis.client import list_or_args
from redis.exceptions import DataError
from .conventions import RedizConventions, REDIZ_CONVENTIONS_ARGS, KeyList, NameList, ValueList
from rediz.utilities import get_json_safe, has_nan, shorten, stem
from pprint import pprint

# ADMIN REDIZ
# -----
# Implements an admin-only API.

PY_REDIS_ARGS = (
'host', 'port', 'db', 'username', 'password', 'socket_timeout', 'socket_keepalive', 'socket_keepalive_options',
'connection_pool', 'unix_socket_path', 'encoding', 'encoding_errors', 'charset', 'errors',
'decode_responses', 'retry_on_timeout', 'ssl', 'ssl_keyfile', 'ssl_certfile', 'ssl_cert_reqs', 'ssl_ca_certs',
'ssl_check_hostname', 'max_connections', 'single_connection_client', 'health_check_interval', 'client_name')
FAKE_REDIS_ARGS = ('decode_responses',)


class AdminRediz(RedizConventions):

    def __init__(self, **kwargs):
        # Set some system parameters
        conventions_kwargs = dict([(k, v) for k, v in kwargs.items() if k in REDIZ_CONVENTIONS_ARGS])
        super().__init__(**conventions_kwargs)
        # Initialize Rediz instance. Expects host, password, port   ... or default to fakeredis
        for k in conventions_kwargs.keys():
            kwargs.pop(k)
        self.client = self.make_redis_client(**kwargs)

    @staticmethod
    def make_redis_client(**kwargs):
        kwargs["decode_responses"] = True  # Strong Rediz convention
        is_real = "host" in kwargs  # May want to be explicit here
        KWARGS = PY_REDIS_ARGS if is_real else FAKE_REDIS_ARGS
        redis_kwargs = dict()
        for k in KWARGS:
            if k in kwargs:
                redis_kwargs[k] = kwargs[k]
        if is_real:
            return redis.StrictRedis(**redis_kwargs)
        else:
            return fakeredis.FakeStrictRedis(**redis_kwargs)

    def add_award(self, write_key, award_dict):
        """
        This will update the user's existing awards with the `award_dict`.
        Args:
            write_key: public identifying key
            award_dict:
                {
                    award_name: amount,
                    ...,
                }
        """
        if self.is_valid_key(write_key):
            write_key = self.shash(write_key)
        curr_award_dict = json.loads(self.client.hget(name=self._AWARDS, key=write_key))
        curr_award_dict.update(award_dict)
        return self.client.hset(name=self._AWARDS, key=write_key, value=json.dumps(curr_award_dict))

    def remove_award(self, write_key, award_name):
        """
        Remove a specific award from the user.
        Args:
            write_key: public identifying key
            award_name
        """
        if self.is_valid_key(write_key):
            write_key = self.shash(write_key)
        curr_award_dict = json.loads(self.client.hget(name=self._AWARDS, key=write_key))
        if award_name in curr_award_dict:
            del curr_award_dict[award_name]
        return self.client.hset(name=self._AWARDS, key=write_key, value=json.dumps(curr_award_dict))
