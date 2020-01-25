from itertools import zip_longest
import fakeredis, os, re, sys, uuid, math, json, redis
from threezaconventions.crypto import random_key
from collections import OrderedDict
from typing import List, Union, Any, Optional
from redis.client import list_or_args

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
        self.client         = self.make_redis_client(**kwargs)   # Real or mock redis client
        self.reserved       = self.make_reserved(**kwargs)       # Dictionary holding reserved item names and prefix conventions
        self.is_valid_key   = kwargs.get("is_valid_key")   or default_is_valid_key
        self.is_valid_name  = kwargs.get("is_valid_name")  or default_is_valid_name
        self.is_valid_value = kwargs.get("is_valid_value") or default_is_valid_value
        self.random_name    = kwargs.get("random_name")    or default_random_name
        self.random_key     = kwargs.get("random_key")     or default_random_key

    def mget(self, names:NameList, *args):
        names = list_or_args(names,args)
        return self.get(names=names)

    def get(self,name:Optional[str]=None,
                 names:Optional[NameList]=None, **nuissance ):
        """ Retrieve value(s). There is no permissioning on read """
        names = names or [ name ]
        res = self._pipelined_get(names=names)
        return res if (name is None) else res[0]

    def mset(self,names:Optional[NameList]=None,
                  values:Optional[ValueList]=None,
                  write_keys:Optional[KeyList]=None, **nuissance):
        return self.set(names=names, values=values, write_keys=write_keys )

    def set(self,names:Optional[NameList]=None,
                 values:Optional[ValueList]=None,
                 write_keys:Optional[KeyList]=None,
                 name:Optional[str]=None,
                 value:Optional[Any]=None,
                 write_key:Optional[str]=None, **nuissance):
        """
                  :param
                  returns:  [ {"name":name, "write_key":write_key} ]  if names is supplied,
        otherwise returns:    {"name":name, "write_key":write_key}    when used in the singular
        """
        singular = names is None
        names, values, write_keys = self._coerce_inputs(names=names,values=values,
                                  write_keys=write_keys,name=name,value=value,write_key=write_key)
        # Execute
        execution_log = self._set( names=names,values=values, write_keys=write_keys )
        # Re-jigger results
        access = self._coerce_outputs( execution_log )
        return access[0] if singular else access

    def delete(self, name=None, write_key=None, names:Optional[NameList]=None, write_keys:Optional[KeyList]=None ):
        """ Permissioned delete """
        names, write_keys = names or [ name ], write_keys or [ write_key ]
        are_valid = self._are_valid_write_keys(names, write_keys)
        authorized_kill_list = [ name for (name,is_valid_write_key) in zip(names,are_valid) if is_valid_write_key ]
        self._delete(*authorized_kill_list)

    def _garbage_collection(self, max_searches=100, survey_fraction=0.1 ):
        """ Randomized search and destroy for expired data """
        num_keys     = self.client.scard(self.reserved["names"])
        num_survey   = int( survey_fraction*num_keys )
        num_searches = max( 1, int( num_survey / 1000 ) )
        orphans = set()
        for _ in range(num_searches):
            orphans.update(self._randomly_find_orphans())
        self._delete(*orphans)

    def _delete(self, names, *args ):
        """ Remove data, subscriptions, messages, ownership and set entry """
        names = list_or_args(names,args)
        self.assert_no_colons(names)
        messages_removal_pipe = self.client.pipeline(transaction=False)
        for name in names:
            subscribers       = self.client.smembers(name=self.reserved["subscribers"]+name)
            for subscriber in subscribers:
                recipient_mailbox = self.reserved["messages"]+name
                messages_removal_pipe.hdel(recipient_mailbox,name)
        messages_removal_pipe.execute()
        self.client.hdel(self.reserved["name_to_key"],*names)
        self.client.delete( *[self.reserved["subscribers"]+name for name in names] )
        self.client.delete( *[self.reserved["messages"]+name for name in names] )
        self.client.delete( *names )
        self.client.srem( self.reserved["names"], *names )

    def _randomly_find_orphans(self,number=1000):
        NAMES = name=self.reserved["names"]
        unique_random_names = list(set(self.client.srandom(NAMES,number)))
        num_random = len(unique_random_names)
        if num_random:
            num_exists = self.client.exists(*random_names)
            if num_exists<number:
                # Must be orphans...
                exists_pipe = self.client.pipeline(transaction=True)
                for name in random_names:
                    exists_pipe.exists(name)
                exists  = exists_pipe.execute()
                orphans = [ name for name,ex in zip(random_names,exists) if not(exists) ]
                return orphans

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
    def _coerce_outputs( execution_log ):
        """ Convert to list of dicts containing names and write keys """
        executed = sorted(execution_log["executed"], key = lambda d: d['ndx'])
        return [ {"name":s["name"],"write_key":s["write_key"]} for s in executed ]

    @staticmethod
    def assert_no_colons(names,*args):
        names = list_or_args(names,args)
        if any( (name is not None) and (":" in name) for name in names):
            raise Exception("Operation attempted with a name that has a colon in it.")

    def _set(self,names:Optional[NameList]=None,
                  values:Optional[ValueList]=None,
                  write_keys:Optional[KeyList]=None,
                  name:Optional[str]=None,
                  value:Optional[Any]=None,
                  write_key:Optional[str]=None, **nuisance):
        # Returns execution log format
        names, values, write_keys = self._coerce_inputs(names,values,write_keys,name,value,write_key)
        ndxs = list(range(len(names)))
        executed_obscure,  rejected_obscure,  ndxs, names, values, write_keys = self._pipelined_set_obscure(  ndxs, names, values, write_keys)
        executed_new,      rejected_new,      ndxs, names, values, write_keys = self._pipelined_set_new(      ndxs, names, values, write_keys)
        executed_existing, rejected_existing                                  = self._pipelined_set_existing( ndxs, names, values, write_keys)
        return {"executed":executed_obscure+executed_new+executed_existing,
                "rejected":rejected_obscure+rejected_new+rejected_existing}

    def _pipelined_get(self,names):
        if len(names):
            get_pipe = self.client.pipeline(transaction=True)
            for name in names:
                get_pipe.get(name=name)
            return get_pipe.execute()

    def _pipelined_set_obscure(self, ndxs, names, values, write_keys):
        # Set values only if names were None. This prompts generation of a randomly chosen obscure name.
        executed      = list()
        rejected      = list()
        ignored_ndxs  = list()
        if ndxs:
            obscure_pipe  = self.client.pipeline(transaction=True)

            for ndx, name, value, write_key in zip( ndxs, names, values, write_keys):
                if not(self.is_valid_value(value)):
                    rejected.append({"ndx":ndx, "name":name,"value":value,"error":"invalid value of type "+type(value)+" was supplied"})
                else:
                    if (name is None):
                        if write_key is None:
                            write_key = self.random_key()
                        if not(self.is_valid_key(write_key)):
                            rejected.append({"ndx":ndx,"name":name,"write_key":write_key,"errror":"invalid write_key"})
                        else:
                            new_name = self.random_name()
                            obscure_pipe, intent = self._new_obscure_page(pipe=obscure_pipe,ndx=ndx, name=new_name,value=value, write_key=write_key)
                            executed.append(intent)
                    elif not(self.is_valid_name(name)):
                        rejected.append({"ndx":ndx, "name":name,"error":"invalid name"})
                    else:
                        ignored_ndxs.append(ndx)

            if len(executed):
                obscure_results = Rediz.pipe_results_grouper( results=obscure_pipe.execute(), n=len(executed) )
                for intent, res in zip(executed,obscure_results):
                    intent.update({"result":res})

        # Marshall residual. Return indexes, names, values and write_keys that are yet to be processed.
        names          = [ n for n,ndx in zip(names, ndxs)       if ndx in ignored_ndxs ]
        values         = [ v for v,ndx in zip(values, ndxs)      if ndx in ignored_ndxs ]
        write_keys     = [ w for w,ndx in zip(write_keys, ndxs)  if ndx in ignored_ndxs ]
        return executed, rejected, ignored_ndxs, names, values, write_keys

    def _pipelined_set_new(self,ndxs, names, values, write_keys):

        executed      = list()
        rejected      = list()
        ignored_ndxs  = list()

        if ndxs:
            exists_pipe = self.client.pipeline(transaction=False)
            for name in names:
                exists_pipe.hexists(name=self.reserved["name_to_key"],key=name)
            exists = exists_pipe.execute()

            new_pipe     = self.client.pipeline(transaction=False)
            for exist, ndx, name, value, write_key in zip( exists, ndxs, names, values, write_keys):
                if not(exist):
                    if write_key is None:
                        write_key = self.random_key()
                    if not(self.is_valid_key(write_key)):
                        rejected.append({"ndx":ndx,"name":name,"write_key":write_key,"errror":"invalid write_key"})
                    else:
                        new_pipe, intent = self._new_page(new_pipe,ndx=ndx, name=name,value=value,write_key=write_key)
                        executed.append(intent)
                else:
                    ignored_ndxs.append(ndx)

            if len(executed):
                new_results = Rediz.pipe_results_grouper( results= new_pipe.execute(), n=len(executed) )
                for intent, res in zip(executed,new_results):
                    intent.update({"result":res})

        # Yet to get to...
        names          = [ n for n,ndx in zip(names, ndxs)       if ndx in ignored_ndxs ]
        values         = [ v for v,ndx in zip(values, ndxs)      if ndx in ignored_ndxs ]
        write_keys     = [ w for w,ndx in zip(write_keys, ndxs)  if ndx in ignored_ndxs ]
        return executed, rejected, ignored_ndxs, names , values, write_keys

    def _are_valid_write_keys(self,names,write_keys):
        return [ k==k1 for (k,k1) in zip( write_keys, self._write_keys(names) ) ]

    def _write_keys(self,names):
        if names:
            return self.client.hmget(name=self.reserved["name_to_key"],keys=names)

    def _pipelined_set_existing(self,ndxs, names,values, write_keys):
        executed     = list()
        rejected     = list()
        if ndxs:
            modify_pipe = self.client.pipeline(transaction=False)
            official_write_keys = self._write_keys(names)
            for ndx,name, value, write_key, official_write_key in zip( ndxs, names, values, write_keys, official_write_keys ):
                if write_key==official_write_key:
                    modify_pipe, intent = self._modify_page(modify_pipe,ndx=ndx,name=name,value=value)
                    intent.update({"write_key":write_key})
                    executed.append(intent)
                else:
                    rejected.append({"name":name,"value":value,"write_key":write_key,"official_write_key_ends_in":official_write_key[-4:],
                    "error":"write_key does not match page_key on record"})

            if len(executed):
                modify_results = Rediz.pipe_results_grouper( results = modify_pipe.execute(), n=len(executed) )
                for intent, res in zip(executed,modify_results):
                    intent.update({"result":res})

        return executed, rejected

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

        return executed

    @staticmethod
    def cost_based_ttl(value):
        # Economic assumptions
        REPLICATION         = 12.                         # Subscribers
        DOLLAR              = 10000.                      # Credits per dollar
        COST_PER_MONTH_10MB = 1.*DOLLAR
        COST_PER_MONTH_1b   = COST_PER_MONTH_10MB/(10*1000*1000)
        SECONDS_PER_DAY     = 60.*60.*24.
        SECONDS_PER_MONTH   = SECONDS_PER_DAY*30.
        FIXED_COST_bytes    = 100                        # Overhead
        MAX_TTL_SECONDS     = int(SECONDS_PER_DAY*7)

        num_bytes = sys.getsizeof(value)
        credits_per_month = REPLICATION*(num_bytes+FIXED_COST_bytes)*COST_PER_MONTH_1b
        ttl_seconds = int( math.ceil( SECONDS_PER_MONTH / credits_per_month ) )
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
    def make_reserved( branch="prod", **ignored ):
        return {"name_to_key":branch+":name_to_key:hash", # Hold write keys
                "names":branch+":names:set",              # Required for random garbage collection
                "subscribers":branch+':subscribers:set:',
                "messages":branch+':messages:hash:'}

    @staticmethod
    def pipe_results_grouper(results,n):
        """ A utility for collecting pipelines where operations are in chunks """
        def grouper(iterable, n, fillvalue=None):
            args = [iter(iterable)] * n
            return zip_longest(*args, fillvalue=fillvalue)

        m = int(len(results)/n)
        return list(grouper(iterable=results,n=m,fillvalue=None))


    def _new_obscure_page( self, pipe, ndx, name, value, write_key):
        pipe, intent = self._new_page( pipe=pipe, ndx=ndx, name=name, value=value, write_key=write_key )
        intent.update({"obscure":True})
        return pipe, intent

    def _new_page( self, pipe, ndx, name, value, write_key ):
        """ Create new page
              pipe         :  Redis pipeline
              intent       :  Explanation in form of a dict
              NAME_TO_KEY  :  Name of Redis hash holding lookup from name --> write_key
        """
        ttl, ttl_days = Rediz.cost_based_ttl(value)
        pipe.hset(name=self.reserved["name_to_key"],key=name,value=write_key)  # Establish ownership
        pipe.sadd(self.reserved["names"],name)                                # Need this for random access
        pipe, intent = Rediz._modify_page(pipe,ndx=ndx,name=name,value=value)
        intent.update({"new":True,"write_key":write_key})
        return pipe, intent

    @staticmethod
    def _modify_page(pipe,ndx,name,value,intent=dict()):
        ttl, ttl_days = Rediz.cost_based_ttl(value)
        intent.update({"ndx":ndx,"name":name,"value":value,"ttl_days":ttl_days,"new":False,"obscure":False})
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
