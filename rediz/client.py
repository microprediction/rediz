from itertools import zip_longest
import fakeredis, os, re, sys, uuid, math, json, redis
from threezaconventions.crypto import random_key
from collections import OrderedDict
from typing import List, Union, Any, Optional

# Implements a simple key-permissioned usage of Redis intended for shared use, with quasi-pub/sub mechanism
#
# Methods
# -------
#   > set, get, delete
#   > subscribe, unsubscribe
#
# Permissioning
# -------------
# Permissioning is achieved by a hash of name->official_write_key. It is first-in-best dressed.
#
# Subscription:
# ------------
# There are hooks built into set() that propagate new values into a recipient subscriber's messages mailbox.
# The mailbox is just a redis hash keyed by sender. If my-node.json subscribes to just-set-me.json then
# a call to set(just-set-me.json) will populate prod-messages::my-node.json or similar.
#
# Performance
# -----------
# All commands accept list arguments and use pipelining to minimize communication with the server.
#
#
# Example:
#
# from rediz import Rediz
# rdz = Rediz()
# names = [ None, None, random_name() ]
# write_keys = [ random_key(), None, 'too-short' ]
# values = [ 8, "cat", json.dumps("dog")]
# result = rdz.set(names=names,write_keys=write_keys,values=values)

PY_REDIS_ARGS = ('host','port','db','username','password','socket_timeout','socket_keepalive','socket_keepalive_options',
                 'connection_pool', 'unix_socket_path','encoding', 'encoding_errors', 'charset', 'errors',
                 'decode_responses', 'retry_on_timeout','ssl', 'ssl_keyfile', 'ssl_certfile','ssl_cert_reqs', 'ssl_ca_certs',
                 'ssl_check_hostname', 'max_connections', 'single_connection_client','health_check_interval', 'client_name')
FAKE_REDIS_ARGS = ('decode_responses',)

KeyList   = List[Optional[str]]
NameList  = List[Optional[str]]
ValueList = List[Optional[Any]]

class Rediz(object):

    def __init__(self,**kwargs):
        self.client         = self.make_redis_client(**kwargs)
        self.reserved       = self.make_reserved(**kwargs)       # Dictionary holding reserved item names and prefix conventions
        self.is_valid_key   = kwargs.get("is_valid_key")   or default_is_valid_key
        self.is_valid_name  = kwargs.get("is_valid_name")  or default_is_valid_name
        self.is_valid_value = kwargs.get("is_valid_value") or default_is_valid_value
        self.random_name    = kwargs.get("random_name")    or default_random_name
        self.random_key     = kwargs.get("random_key")     or default_random_key

    def get(self,names:Optional[NameList]=None, name:Optional[str]=None, **ignored ):
        """ Retrieve value(s) """
        names = names or [ name ]
        res = self._pipelined_get(names=names)
        return res if (name is None) else res[0]

    def set(self,names:Optional[NameList]=None,
                 values:Optional[ValueList]=None,
                 write_keys:Optional[KeyList]=None,
                 name:Optional[str]=None,
                 value:Optional[Any]=None,
                 write_key:Optional[str]=None, **ignored):
        """
                  :param
                  returns:  [ {"name":name, "write_key":write_key} ]  if names is supplied,
        otherwise returns:    {"name":name, "write_key":write_key}    when used in the singular
        """

        # Permit singleton or vector call
        names, values, write_keys = self._coerce_inputs(names=names,values=values,
                                  write_keys=write_keys,name=name,value=value,write_key=write_key)
        original_names = [ n for n in names ]
        # Execute
        execution_log = self._set( names=names,values=values, write_keys=write_keys )
        # Re-jigger results
        succinct = self._coerce_outputs( execution_log, original_names )
        return succinct if (name is None) else succinct[0]

    @staticmethod
    def _coerce_inputs(  names:Optional[NameList]=None,
                         values:Optional[ValueList]=None,
                         write_keys:Optional[KeyList]=None,
                         name:Optional[str]=None,
                         value:Optional[Any]=None,
                         write_key:Optional[str]=None):
        # Convert singletons to arrays, broadcasting as necessary
        names  = names or [ name ]
        values = values or [ value for _ in names ]
        write_keys = write_keys or [ write_key for _ in names ]
        return names, values, write_keys

    @staticmethod
    def _coerce_outputs( execution_log, names=None ):
        """ Convert to list of dict, so that this style is possible:

              access = {"name":"whatever","write_key":"blah"}
              access = rdz.set(value=value, **access)
              rdz.get(**access)

        """
        if names is not None:
            ordered = OrderedDict(zip(names, [ None for _ in names ]))
        for ex in execution_log["executed"]:
            ex_name = ex["name"]
            ex_write_key = ex["write_key"]
            if ex_name in ordered:
                ordered[ex_name]=ex_write_key
        return [ {"name":nm,"write_key":wk} for nm,wk in ordered.items() ]

    def _set(self,names:Optional[NameList]=None,
                  values:Optional[ValueList]=None,
                  write_keys:Optional[KeyList]=None,
                  name:Optional[str]=None,
                  value:Optional[Any]=None,
                  write_key:Optional[str]=None, **ignored):
        # Returns execution log format
        names, values, write_keys = self._coerce_inputs(names,values,write_keys,name,value,write_key)
        executed_obscure,  rejected_obscure,  names, values, write_keys = self._pipelined_set_obscure(names, values, write_keys)
        executed_new,      rejected_new,      names, values, write_keys = self._pipelined_set_new(names, values, write_keys)
        executed_existing, rejected_existing, names, values, write_keys = self._pipelined_set_existing(names, values, write_keys)
        return {"executed":executed_obscure+executed_new+executed_existing,
                "rejected":rejected_obscure+rejected_new+rejected_existing,
                "ignored" :names}

    def _pipelined_get(self,names):
        # Prepare redis pipeline
        if len(names):
            get_pipe = self.client.pipeline(transaction=True)
            for name in names:
                get_pipe.get(name=name)
            return get_pipe.execute()

    def _pipelined_set_obscure(self,names, values, write_keys):
        # Prepare redis pipeline
        obscure_pipe = self.client.pipeline(transaction=True)
        executed     = list()
        rejected     = list()
        pending      = list()
        for name, value, write_key in zip( names, values, write_keys):
            if not(self.is_valid_value(value)):
                rejected.append({"name":name,"value":value,"error":"invalid value of type "+type(value)+" was supplied"})
            else:
                if (name is None):
                    if write_key is None:
                        write_key = self.random_key()
                    if not(self.is_valid_key(write_key)):
                        rejected.append({"name":name,"write_key":write_key,"errror":"invalid write_key"})
                    else:
                        new_name = self.random_name()
                        obscure_pipe, intent = self._new_obscure_page(pipe=obscure_pipe,name=new_name,value=value,
                                                  write_key=write_key, name_to_key=self.reserved["name_to_key"])
                        executed.append(intent)
                elif not(self.is_valid_name(name)):
                    rejected.append({"name":name,"error":"invalid name"})
                else:
                    pending.append(name)

        if len(executed):
            obscure_results = Rediz.pipe_results_grouper( results=obscure_pipe.execute(), n=len(executed) )
            for intent, res in zip(executed,obscure_results):
                intent.update({"result":res})

        # Marshall residual. Return name, values and write_keys that are yet to be processed.
        values         = [ v for v,n in zip(values, names) if n in pending ]
        write_keys     = [ w for w,n in zip(write_keys, names) if n in pending ]
        return executed, rejected, pending, values, write_keys

    def _pipelined_set_new(self,names, values, write_keys):

        exists_pipe = self.client.pipeline(transaction=False)
        for name in names:
            exists_pipe.hexists(name=self.reserved["name_to_key"],key=name)
        exists = exists_pipe.execute()

        executed     = list()
        rejected     = list()
        pending      = list()
        new_pipe     = self.client.pipeline(transaction=False)
        for exist, name, value, write_key in zip( exists, names, values, write_keys):
            if not(exist):
                if write_key is None:
                    write_key = self.random_key()
                if not(self.is_valid_key(write_key)):
                    rejected.append({"name":name,"write_key":write_key,"errror":"invalid write_key"})
                else:
                    new_pipe, intent = self._new_page(new_pipe,name=name,value=value,
                                write_key=write_key,name_to_key=self.reserved["name_to_key"])
                    executed.append(intent)
            else:
                pending.append(name)

        if len(executed):
            new_results = Rediz.pipe_results_grouper( results= new_pipe.execute(), n=len(executed) )
            for intent, res in zip(executed,new_results):
                intent.update({"result":res})

        values         = [ v for v,n in zip(values, names) if n in pending ]
        write_keys     = [ w for w,n in zip(write_keys, names) if n in pending ]
        return executed, rejected, pending, values, write_keys


    def _pipelined_set_existing(self,names,values, write_keys):

        keys_pipe = self.client.pipeline(transaction=False)
        for name in names:
            keys_pipe.hget(name=self.reserved["name_to_key"],key=name)
        official_write_keys = keys_pipe.execute()

        executed     = list()
        rejected     = list()
        pending      = list()

        modify_pipe = self.client.pipeline(transaction=False)
        for name, value, write_key, official_write_key in zip( names, values, write_keys, official_write_keys ):
            if write_key==official_write_key:
                modify_pipe, intent = _modify_page(modify_pipe,name=name,value=value)
                executed.append(intent)
            else:
                rejected.append({"name":name,"value":value,"write_key":write_key,"official_write_key_ends_in":official_write_key[-4:],
                "error":"write_key does not match page_key on record"})

        if len(executed):
            modify_results = pipe_results_grouper( results = modify_pipe.execute(), n=len(executed) )
            for intent, res in zip(executed,modify_results):
                intent.update({"result":res})

        values         = [ v for v,n in zip(values, names) if n in pending ]
        write_keys     = [ w for w,n in zip(write_keys, names) if n in pending ]
        return executed, rejected, pending, values, write_keys

    def _propagate_to_subscribers(self,names,values):

        subscriber_pipe = self.client.pipeline(transaction=False)
        for name in names:
            subscriber_set_name = self.reserved["subscribers::"]+name
            subs = subscriber_pipe.smembers(name=subscriber_set_name)
        subscribers_sets = subscriber_pipe.execute()

        propagate_pipe = self.client.pipeline(transaction=False)

        executed = list()
        for sender_name, value,subscribers_set in zip(names, values,subscribers_sets):
            for subscriber in subscribers_set:
                mailbox_name = self.reserved["messages"]+subscriber
                propagate_pipe.hset(name=mailbox_name,key=sender_name, value=value)
                executed.append({"mailbox_name":mailbox_name,"sender":sender_name,"value":value})

        if len(executed):
            propagation_results = pipe_results_grouper( results = propagate_pipe.execute(), n=len(executed) ) # Overkill while there is 1 op
            for intent, res in zip(executed,propagation_results):
                intent.update({"result":res})

        values         = [ v for v,n in zip(values, names) if n in pending ]
        write_keys     = [ w for w,n in zip(write_keys, names) if n in pending ]
        return executed, rejected, pending, values, write_keys

    @staticmethod
    def cost_based_ttl(value):
        # Economic assumptions
        REPLICATION         = 12.                         # Subscribers
        DOLLAR              = 10000.                      # Credits per dollar
        COST_PER_MONTH_10MB = 1.*DOLLAR
        COST_PER_MONTH_1b   = COST_PER_MONTH_10MB/(10*1000*1000)
        SECONDS_PER_DAY     = 60.*60.*24.
        SECONDS_PER_MONTH   = SECONDS_PER_DAY*30.
        FIXED_COST_bytes    = 1000                        # Overhead
        MAX_TTL_SECONDS     = SECONDS_PER_DAY*7

        num_bytes = sys.getsizeof(value)
        credits_per_month = REPLICATION*(num_bytes+FIXED_COST_bytes)*COST_PER_MONTH_1b
        ttl_seconds = math.ceil( SECONDS_PER_MONTH / credits_per_month )
        ttl_seconds = min(ttl_seconds,MAX_TTL_SECONDS)
        ttl_days = ttl_seconds / SECONDS_PER_DAY
        return ttl_seconds, ttl_days

    @staticmethod
    def make_redis_client(**kwargs):
        kwargs["decode_responses"] = True   # Strong rediz convention
        is_real = "host" in kwargs          # May want to be explicit here
        KWARGS = PY_REDIS_ARGS if is_real else FAKE_REDIS_ARGS
        redis_kwargs = dict()
        for k in KWARGS:
            if k in kwargs:
                redis_kwargs[k]=kwargs[k]
        if is_real:
            return redis.StrictRedis(**redis_kwargs)
        else:
            return fakeredis.FakeStrictRedis(**redis_kwargs)

    @staticmethod
    def make_reserved(branch="prod",
                    name_to_key="hash:rediz-name_to_key",
                    subscribers="rediz-subscribers:",
                    messages="rediz-messages:",
                    **ignored):
        return {"name_to_key":branch+"-"+name_to_key,
                "subscribers":branch+'-'+subscribers,
                "messages":branch+'-'+messages}

    @staticmethod
    def pipe_results_grouper(results,n):
        """ A utility for collecting pipelines where operations are in chunks """
        def grouper(iterable, n, fillvalue=None):
            args = [iter(iterable)] * n
            return zip_longest(*args, fillvalue=fillvalue)

        m = int(len(results)/n)
        return list(grouper(iterable=results,n=m,fillvalue=None))


    @staticmethod
    def _new_obscure_page( pipe, name, value,write_key, name_to_key ):
        pipe, intent = Rediz._new_page( pipe=pipe, name=name, value=value, write_key=write_key, name_to_key=name_to_key )
        intent.update({"obscure":True})
        return pipe, intent

    @staticmethod
    def _new_page(pipe,name,value,write_key, name_to_key):
        """ Create new page
              pipe         :  Redis pipeline
              intent       :  Explanation in form of a dict
              name_to_key  :  Name of Redis hash holding lookup from name --> write_key
        """
        ttl, ttl_days = Rediz.cost_based_ttl(value)
        pipe.hset(name=name_to_key,key=name,value=write_key)     # Establish ownership
        pipe, intent = Rediz._modify_page(pipe,name=name,value=value)
        intent.update({"new":True,"write_key":write_key})
        return pipe, intent

    @staticmethod
    def _modify_page(pipe,name,value,intent=dict()):
        ttl, ttl_days = Rediz.cost_based_ttl(value)
        intent.update({"name":name,"value":value,"ttl":ttl,"ttl_days":ttl_days,"new":False,"obscure":False})
        pipe.set(name=name,value=value,ex=ttl)
        return pipe, intent



# Default rules
def default_random_name():
    return random_key()+'.json'

def default_is_valid_name(name:str):
    name_regex = re.compile(r'^[-a-zA-Z0-9_.]{1,200}$',re.IGNORECASE)
    return (re.match(name_regex, name) is not None) and default_has_valid_extension(name)

def default_is_valid_value(value):
    return sys.getsizeof(value)<100000

def default_is_valid_key(key):
    return isinstance(key,str) and len(key)==len(str(uuid.uuid4()))

def default_has_valid_extension(name):
    stem, ext = os.path.splitext(name)
    return ext in ['.json','.JSON','.html','.HTML']

def default_random_key():
    return random_key()
