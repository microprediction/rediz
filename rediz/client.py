from itertools import zip_longest
import fakeredis, sys, math, json, redis, time, random, itertools
import numpy as np
from collections import Counter
from typing import List, Union, Any, Optional
from redis.client import list_or_args
from .conventions import RedizConventions, KeyList, NameList, Value, ValueList, DelayList

# REDIZ
# -----
# Implements a write-permissioned shared REDIS value store with subscription, history, prediction, clearing
# and delay mechanisms. Intended for collectivized short term (e.g. 5 seconds or 15 minutes) prediction.

PY_REDIS_ARGS = ('host','port','db','username','password','socket_timeout','socket_keepalive','socket_keepalive_options',
                 'connection_pool', 'unix_socket_path','encoding', 'encoding_errors', 'charset', 'errors',
                 'decode_responses', 'retry_on_timeout','ssl', 'ssl_keyfile', 'ssl_certfile','ssl_cert_reqs', 'ssl_ca_certs',
                 'ssl_check_hostname', 'max_connections', 'single_connection_client','health_check_interval', 'client_name')
FAKE_REDIS_ARGS = ('decode_responses',)

DEBUGGING = True
def dump(obj,name="tmp_client.json"):
    if DEBUGGING:
        json.dump(obj,open(name,"w"))

class Rediz(RedizConventions):

    # Initialization

    def __init__(self,**kwargs):
        super(RedizConventions, self).__init__()
        self.SEP = RedizConventions.sep()

        # Rediz instance. Expects host, password, port   If not supplied it may use fakeredis
        self.client         = self.make_redis_client(**kwargs)                 # Real or mock redis client

        # Implementation details: private reserved redis keys and prefixes
        self._obscurity     = ( kwargs.get("obscurity") or "09909-OBSCURE-c94748" ) + self.SEP
        self.JACKPOT        = self._obscurity+"jackpot"                     # Rarely used
        self.OWNERSHIP      = self._obscurity+"ownership"                   # Official map from name to write_key
        self.NAMES          = self._obscurity+"names"                       # Redundant set of all names (needed for random sampling when collecting garbage)
        self.PROMISES       = self._obscurity+"promises"+self.SEP           # Prefixes queues of operations that are indexed by epoch second
        self.POINTER        = self._obscurity+"pointer"                     # A convention used in history stream
        self.BALANCES       = self._obscurity+"balance" + self.SEP          # Hash of all balances attributed to write_keys
        self.PREDICTIONS    = self._obscurity+"predictions" + self.SEP      # Prefix to a listing of contemporaneous predictions by horizon. Must be private as this contains write_keys !
        self.OWNERS         = "owners" + self.SEP           # Prefix to a redundant listing of contemporaneous prediction owners by horizon. Must be private as this contains write_keys !
        self.SAMPLES        = self._obscurity+"samples" + self.SEP          # Prefix to delayed predictions by horizon. Contain write_keys !
        self.ERRORS         = "errors" + self.SEP
        self.PROMISED       = "promised" + self.SEP                         # Prefixes temporary values referenced by the promise queue

        # User facing conventions: transparent use of prefixing
        self.DELAYED        = "delayed"+self.SEP
        self.LINKS          = "links"+self.SEP
        self.BACKLINKS      = "backlinks"+self.SEP
        self.MESSAGES       = "messages"+self.SEP
        self.HISTORY        = "history"+self.SEP
        self.HISTORY_LEN    = int( kwargs.get("history_len") or 1000 )
        self.LAGGED         = "lagged"+self.SEP
        self.LAGGED_TIME    = "times"+self.SEP + "lagged" + self.SEP
        self.LAGGED_LEN     = int( kwargs.get("lagged_len") or 10000 )
        self.SUBSCRIBERS    = "subscribers"+self.SEP
        self.SUBSCRIPTIONS  = "subscriptions"+self.SEP

        # Config
        self.DELAY_SECONDS    = kwargs.get("delay_seconds")  or [1,2,5,10,30,60,2*60,5*60,10*60,15*60, 20*60,30*60, 60*60]
        self.NOISE            = 1.0e-6                                  # Tie-breaking noise added to predictions
        self.DIRAC_NOISE      = 1.0                                     # Noise added for self-prediction
        self.WINDOWS          = [1e-3,1e-2,1.0,100.]                    # Sizes of neighbourhoods around truth
        self.INSTANT_RECALL   = kwargs.get("instant_recall") or False   # Delete messages already sent when sender is deleted?
        self.ERROR_TTL        = int( kwargs.get('error_ttl') or 60*5 )  # Number of seconds that set execution error logs are persisted
        self.DELAY_GRACE      = int( kwargs.get("delay_grace") or 60 )  # Seconds beyond the schedule time when promise data expires
        self.NUM_PREDICTIONS  = int( kwargs.get("num_predictions") or 1000 )  # Number of scenerios in a prediction batch



    # Public interface: Reading without authorization

    def card(self):
        return self.client.scard(self.NAMES)

    def exists(self, names, *args):
        names = list_or_args(names, args)
        return self.client.exists(*names)

    def get(self, name):
        return self._get_implementation( name = name )

    def mget(self, names:NameList, *args):
        names = list_or_args(names,args)
        return self._get_implementation( names=names )

    def get_samples(self, name, delay=None, delays=None):
        return self._get_samples_implementation(name=name, delay=delay, delays=delays )

    def get_jackpot(self):
        return float( self.client.hget(self.BALANCES,self.JACKPOT) or 0 )

    def get_delayed(self, names, delay=None, delays=None, to_float=True):
        return self._get_delayed_implementation( names=names, delay=delay, delays=delays, to_float=to_float)

    def get_lagged(self, name, start=0, end=None, count=None, with_times=False, to_float=True ):
        return self._get_lagged_implementation(name=name, start=start, end=end, count=count, with_times=with_times, to_float=True)

    def get_balance(self, write_key ):
        return self._get_balance_implementation(write_key=write_key)

    def mget_balance(self, write_keys, aggregate=True):
        return self._get_balance_implementation(write_keys=write_keys, aggregate=aggregate)

    def get_history(self, name, max='+', min='-', count=None, populate=True, drop_expired=True ):
        return self._get_history_implementation( name=name, max=max, min=min, count=None, populate=True, drop_expired=True )

    # Public interface: Streaming and predicting

    def set( self, name, value, write_key ):
        return self._set_implementation(name=name, value=value, write_key=write_key, return_args=None, budget=1 )

    def mset(self,names:NameList, values:ValueList, write_keys:KeyList):
        return self._set_implementation(names=names, values=values, write_keys=write_keys, return_args=None, budget=1000 )

    def new( self, name=None, value=None, write_key=None ):
        """ For when you don't want to generate write_key (or value, or name)"""
        supplied = zip( ("name","value","write_key"), (name is not None, value is not None, write_key is not None) )
        return_args = [ a for a,s in supplied if not(s) ]
        return self._set_implementation(name=name, value=value or "", write_key=write_key, return_args=return_args, budget=1)

    def delete(self, name, write_key):
        return self._delete_implementation( name=name, write_key=write_key )

    def mdelete(self, names, write_key:Optional[str]=None, write_keys:Optional[KeyList]=None):
        return self._delete_implementation( names=names, write_key=write_key, write_keys=write_keys )

    def predict(self, name, values, write_key ):
        return self._predict_implementation( name, values, write_key )


    # Public interface: Subscription

    def subscriptions(self, name, write_key):
        """ Permissioned listing of current subscriptions """
        return self._subscriptions_implementation(name=name, write_key=write_key )

    def subscribers(self, name, write_key):
        """ Permissioned listing of who is subscribing to name """
        return self._subscribers_implementation(name=name, write_key=write_key )

    def subscribe(self, name, write_key, source, delay=0):
        """ Permissioned subscribe """
        return self._subscribe_implementation(name=name, write_key=write_key, source=source, delay=delay )

    def msubscribe(self, name, write_key, sources, delay:int=None, delays:Optional[DelayList]=None):
        """ Permissioned subscribe to multiple sources """
        return self._subscribe_implementation(name=name, write_key=write_key, sources=sources, delay=delay, delays=delays )

    def unsubscribe(self, name, write_key, source, delays=None):
        return self._unsubscribe_implementation(name=name, write_key=write_key, source=source, delays=delays )

    def munsubscribe(self, name, write_key, sources, delays=None):
        return self._unsubscribe_implementation(name=name, write_key=write_key, sources=sources, delays=delays )

    def messages(self, name, write_key):
        """ Use key to open the mailbox """
        return self._messages_implementation(name=name,write_key=write_key)

    # Public interface: Linking

    def link(self, name, write_key, target ):
        """ Owner of name can link to a target from any delay:: """
        return self._link_implementation(name=name, write_key=write_key, budget=1, target=target )

    def mlink(self, name, write_key, targets, strict=False):
        """ Permissioned link to multiple targets """
        return self._link_implementation(name=name, write_key=write_key, budget=1000, targets=targets )

    def unlink(self, name, write_key, target):
        """ Permissioned removal of link (either party can do this) """
        return self._unlink_implementation(name=name, write_key=write_key, target=target )

    def links(self, name, write_key):
        """ Permissioned listing of targets """
        return self._links_implementation(name=name, write_key=write_key )

    def backlinks(self, name, write_key):
        """ Permissioned listing of backlinks (predictors) of a target """
        return self._backlinks_implementation(name=name, write_key=write_key )


    # --------------------------------------------------------------------------
    #            Implementation  (set)
    # --------------------------------------------------------------------------

    def _set_implementation(self,budget, names:Optional[NameList]=None,
                 values:Optional[ValueList]=None,
                 write_keys:Optional[KeyList]=None,
                 name:Optional[str]=None,
                 value:Optional[Any]=None,
                 write_key:Optional[str]=None,
                 return_args:Optional[List[str]]=None):
        singular = (names is None) and (values is None) and (write_keys) is None
        names, values, write_keys = self._coerce_inputs(names=names,values=values,
                        write_keys=write_keys,name=name,value=value,write_key=write_key)
        # Encode
        values = [ v if isinstance(v,(int,float,str)) else json.dumps(v) for v in values ]

        # Execute and create temporary logs
        execution_log = self._pipelined_set( names=names,values=values, write_keys=write_keys, budget=budget )

        if len(values)==1 and isinstance( values[0], (int,float) ):
            # Seed the nano-markets and settle the existing ones.
            self._dirac(  name=name, value=values[0], write_key=write_keys[0] )
            self._settle( name=name, value=values[0] )

        # Re-jigger results
        if return_args is not None:
            access = self._coerce_outputs( execution_log=execution_log, return_args=return_args )
            return access[0] if singular else access
        else:
            access = self._coerce_outputs( execution_log=execution_log, return_args=('write_key',) )
            return sum( (a["write_key"] is not None) for a in access )

    def _pipelined_set(self, names:Optional[NameList]=None,
                  values:Optional[ValueList]=None,
                  write_keys:Optional[KeyList]=None,
                  name:Optional[str]=None,
                  value:Optional[Any]=None,
                  write_key:Optional[str]=None,
                  budget=1):
        # Returns execution log format   FIXME: Why twice?? Fix old tests and get rid of this
        names, values, write_keys = self._coerce_inputs(names=names,values=values,write_keys=write_keys,
                                                        name=name,value=value,write_key=write_key)
        ndxs = list(range(len(names)))
        multiplicity = len(names)

        ttl  = self.cost_based_ttl(budget=budget,multiplicity=multiplicity,values=values)
        executed_obscure,  rejected_obscure,  ndxs, names, values, write_keys = self._pipelined_set_obscure(  ndxs=ndxs, names=names, values=values, write_keys=write_keys, ttl=ttl)
        executed_new,      rejected_new,      ndxs, names, values, write_keys = self._pipelined_set_new(      ndxs=ndxs, names=names, values=values, write_keys=write_keys, ttl=ttl)
        executed_existing, rejected_existing                                  = self._pipelined_set_existing( ndxs=ndxs, names=names, values=values, write_keys=write_keys, ttl=ttl)

        executed = executed_obscure+executed_new+executed_existing

        # Propagate to subscribers
        modified_names  = [ ex["name"] for ex in executed ]
        modified_values = [ ex["value"] for ex in executed ]

        self._propagate_to_subscribers( names = modified_names, values = modified_values )
        return {"executed":executed,
                "rejected":rejected_obscure+rejected_new+rejected_existing}

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
    def _coerce_outputs( execution_log, return_args=None ):
        """ Convert to list of dicts containing names and write keys """
        if return_args is None:
            return_args = ('name','write_key')
        sorted_log = sorted(execution_log["executed"]+execution_log["rejected"], key = lambda d: d['ndx'])
        return [  dict( (arg,s[arg]) for arg in return_args ) for s in sorted_log ]

    def _pipelined_get(self,names):
        if len(names):
            get_pipe = self.client.pipeline(transaction=True)
            for name in names:
                get_pipe.get(name=name)
            return get_pipe.execute()

    def _pipelined_set_obscure(self, ndxs, names, values, write_keys, ttl):
        # Set values only if names were None. This prompts generation of a randomly chosen obscure name.
        executed      = list()
        rejected      = list()
        ignored_ndxs  = list()
        if ndxs:
            obscure_pipe  = self.client.pipeline(transaction=True)

            for ndx, name, value, write_key in zip( ndxs, names, values, write_keys):
                if not(self.is_valid_value(value)):
                    rejected.append({"ndx":ndx, "name":name,"write_key":None,"value":value,"error":"invalid value of type "+str(type(value))+" was supplied"})
                else:
                    if name is None:
                        if write_key is None:
                            write_key = self.random_key()
                        if not(self.is_valid_key(write_key)):
                            rejected.append({"ndx":ndx,"name":name,"write_key":None,"errror":"invalid write_key"})
                        else:
                            new_name = self.random_name()
                            obscure_pipe, intent = self._new_obscure_page(pipe=obscure_pipe,ndx=ndx, name=new_name,value=value, write_key=write_key, ttl=ttl )
                            executed.append(intent)
                    elif not(self.is_valid_name(name)):
                        rejected.append({"ndx":ndx, "name":name,"write_key":None, "error":"invalid name"})
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

    def _pipelined_set_new(self,ndxs, names, values, write_keys, ttl):
        # Treat cases where name does not exist yet
        executed      = list()
        rejected      = list()
        ignored_ndxs  = list()

        if ndxs:
            exists_pipe = self.client.pipeline(transaction=False)
            for name in names:
                exists_pipe.hexists(name=self.OWNERSHIP,key=name)
            exists = exists_pipe.execute()

            new_pipe     = self.client.pipeline(transaction=False)
            for exist, ndx, name, value, write_key in zip( exists, ndxs, names, values, write_keys):
                if not(exist):
                    if write_key is None:
                        write_key = self.random_key()
                    if not(self.is_valid_key(write_key)):
                        rejected.append({"ndx":ndx,"name":name,"write_key":None,"errror":"invalid write_key"})
                    else:
                        new_pipe, intent = self._new_page(new_pipe,ndx=ndx, name=name,value=value,write_key=write_key,ttl=ttl)
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

    def _authorize(self,name,write_key):
        return write_key==self._authority(name=name)

    def _mauthorize(self,names,write_keys):
        authority = self._mauthority(names)
        assert len(names)==len(write_keys)
        comparison = [ k==k1 for (k,k1) in zip( write_keys, authority ) ]
        return comparison

    def _authority(self,name):
        root = self._root_name(name)
        return self.client.hget(self.OWNERSHIP,root)

    def _mauthority(self,names, *args):
        names = list_or_args(names,args)
        return self.client.hmget(self.OWNERSHIP,*names)

    def _pipelined_set_existing(self,ndxs, names,values, write_keys, ttl):
        executed     = list()
        rejected     = list()
        if ndxs:
            modify_pipe         = self.client.pipeline(transaction=False)
            error_pipe          = self.client.pipeline(transaction=False)
            official_write_keys = self._mauthority(names)
            for ndx,name, value, write_key, official_write_key in zip( ndxs, names, values, write_keys, official_write_keys ):
                if write_key==official_write_key:
                    modify_pipe, intent = self._modify_page(modify_pipe,ndx=ndx,name=name,value=value,ttl=ttl)
                    intent.update({"ndx":ndx,"write_key":write_key})
                    executed.append(intent)
                else:
                    auth_message = {"ndx":ndx,"name":name,"value":value,"write_key":write_key,"official_write_key_ends_in":official_write_key[-4:],
                    "error":"write_key does not match page_key on record"}
                    intent = auth_message
                    error_pipe.append(self.ERRORS + write_key, json.dumps(auth_message))
                    error_pipe.expire(self.ERRORS + write_key, self.ERROR_TTL)
                    rejected.append(intent)
            if len(executed):
                modify_results = Rediz.pipe_results_grouper( results = modify_pipe.execute(), n=len(executed) )
                for intent, res in zip(executed,modify_results):
                    intent.update({"result":res})

            if len(rejected):
                error_pipe.execute()

        return executed, rejected

    def _propagate_to_subscribers(self,names,values):
        subscriber_pipe = self.client.pipeline(transaction=False)
        for name in names:
            subscriber_set_name = self.SUBSCRIBERS+name
            subs = subscriber_pipe.smembers(name=subscriber_set_name)
        subscribers_sets = subscriber_pipe.execute()

        propagate_pipe = self.client.pipeline(transaction=False)

        executed = list()
        for sender_name, value,subscribers_set in zip(names, values,subscribers_sets):
            for subscriber in subscribers_set:
                mailbox_name = self.MESSAGES+subscriber
                propagate_pipe.hset(name=mailbox_name,key=sender_name, value=value)
                executed.append({"mailbox_name":mailbox_name,"sender":sender_name,"value":value})

        if len(executed):
            propagation_results = Rediz.pipe_results_grouper( results = propagate_pipe.execute(), n=len(executed) ) # Overkill while there is 1 op
            for intent, res in zip(executed,propagation_results):
                intent.update({"result":res})

        return executed


    @staticmethod
    def cost_based_ttl(values,multiplicity:int=1,budget:int=1):
        # Assign a time to live based on random sampling of the size of values stored.
        # A vector of 100 floats lasts a week.
        # A vector of 1000 floats lasts a day.
        REPLICATION         = 3.                          # History, Buffer
        DOLLAR              = 10000.                      # Credits per dollar
        COST_PER_MONTH_10MB = 1.*DOLLAR
        COST_PER_MONTH_1b   = COST_PER_MONTH_10MB/(10*1000*1000)
        SECONDS_PER_DAY     = 60.*60.*24.
        SECONDS_PER_MONTH   = SECONDS_PER_DAY*30.
        FIXED_COST_bytes    = 100                        # Overhead
        MAX_TTL_SECONDS     = int(SECONDS_PER_DAY*7)

        if len(values):
            if len(values)<10:
                value_sample = values
            else:
                value_sample = random.sample(values,10)
            num_bytes = max( (sys.getsizeof(value) for value in values) )

            credits_per_month = multiplicity*REPLICATION*(num_bytes+FIXED_COST_bytes)*COST_PER_MONTH_1b
            ttl_seconds = int( math.ceil( SECONDS_PER_MONTH / credits_per_month ) )
            ttl_seconds = budget*ttl_seconds
            ttl_seconds = min(ttl_seconds,MAX_TTL_SECONDS)
            return ttl_seconds
        return 1

    @staticmethod
    def make_redis_client(**kwargs):
        kwargs["decode_responses"] = True   # Strong Rediz convention
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

    def admin_garbage_collection(self, fraction=0.01 ):
        """ Randomized search and destroy for expired data """
        num_keys     = self.client.scard(self.NAMES)
        num_survey   = min( 100, max( 20, int( fraction*num_keys ) ) )
        orphans      = self._randomly_find_orphans( num=num_survey )
        if orphans is not None:
            self._delete(*orphans)
            return len(orphans)
        else:
            return 0



    def _randomly_find_orphans(self,num=1000):
        NAMES = self.NAMES
        unique_random_names = list(set(self.client.srandmember(NAMES,num)))
        num_random = len(unique_random_names)
        if num_random:
            num_exists = self.client.exists(*unique_random_names)
            if num_exists<num_random:
                # There must be orphans, defined as those who are listed
                # in reserved["names"] but have expired
                exists_pipe = self.client.pipeline(transaction=True)
                for name in unique_random_names:
                    exists_pipe.exists(name)
                exists  = exists_pipe.execute()

                orphans = [ name for name,ex in zip(unique_random_names,exists) if not(ex) ]
                return orphans

    @staticmethod
    def pipe_results_grouper(results,n):
        """ A utility for collecting pipelines where operations are in chunks """
        def grouper(iterable, n, fillvalue=None):
            args = [iter(iterable)] * n
            return zip_longest(*args, fillvalue=fillvalue)

        m = int(len(results)/n)
        return list(grouper(iterable=results,n=m,fillvalue=None))


    def _new_obscure_page( self, pipe, ndx, name, value, write_key, ttl):
        pipe, intent = self._new_page( pipe=pipe, ndx=ndx, name=name, value=value, write_key=write_key, ttl=ttl )
        intent.update({"obscure":True})
        return pipe, intent

    def _new_page( self, pipe, ndx, name, value, write_key, ttl ):
        """ Create new page
              pipe         :  Redis pipeline
              intent       :  Explanation in form of a dict
              ttl          :  Time to live in seconds
        """
        pipe.hset(name=self.OWNERSHIP,key=name,value=write_key)  # Establish ownership
        pipe.sadd(self.NAMES,name)                                # Need this for random access
        pipe, intent = self._modify_page(pipe=pipe,ndx=ndx,name=name,value=value,ttl=ttl)
        intent.update({"new":True,"write_key":write_key,"value":value})
        return pipe, intent

    def _streams_support(self):
        # Streams not supported on fakeredis
        try:
            record_of_test = {"time":str(time.time()) }
            self.client.xadd(name='e5312d16-dc87-46d7-a2e5-f6a6225e63a5',fields=record_of_test)
            return True
        except:
            return False



    def _promised_name(self, name):
        return self.PROMISED + self.random_key()[:8] + self.SEP + name[:14]

    def _modify_page(self, pipe,ndx,name,value,ttl):
        """ Create pipelined operations for save, buffer, history etc """

        # (1) Set the actual value ... which will soon be overwritten ... and a randomly generated copy
        pipe.set(name=name,value=value,ex=ttl)
        name_of_copy = self._promised_name(name)
        HISTORY_TTL = min(max(2 * 60 * 60, ttl), 60 * 60 * 24)
        pipe.set(name=name_of_copy, value=value, ex=HISTORY_TTL)

        # (2) Write history log stream and buffers which may or may not include value field(s)
        if self._streams_support():
            if self.is_small_value():
                fields = RedizConventions.to_record(value)
            else:
                fields = {self.POINTER: name_of_copy}
            pipe.xadd(name=self.HISTORY + name, fields=fields)
            pipe.xtrim(name=self.HISTORY + name, maxlen=self.HISTORY_LEN)

        # (3) For scalar and vector only, write to simple buffer lists
        if self.is_scalar_value(value) or self.is_vector_value(value) and self.is_small_value(value):
            t = time.time()
            pipe.lpush(self.LAGGED+name,value)
            pipe.lpush(self.LAGGED_TIME+name, t)
            pipe.ltrim(name=self.LAGGED+name,start=0,end=self.LAGGED_LEN)

        # (4) Construct delay promises
        utc_epoch_now = int(time.time())
        for delay in self.DELAY_SECONDS:
            queue       = self._promise_queue_name( utc_epoch_now+delay )            # self.PROMISES+str(utc_epoch_now+delay)
            destination = self._delayed_name( name=name, delay=delay )               # self.DELAYED+str(delay_seconds)+self.SEP+name
            promise     = self._copy_promise(source=name_of_copy, destination=destination)
            pipe.sadd( queue, promise )
            pipe.expire( name=queue, time=delay+self.DELAY_GRACE)

        # (5) Execution log
        intent = {"ndx":ndx,"name":name,"value":value,"ttl":ttl,
                  "new":False,"obscure":False,"copy":name_of_copy}

        return pipe, intent

    def _copy_promise(self, source, destination ):
        return source+self.SEP+'copy'+self.SEP+destination

    def _delayed_name(self, name, delay ):
        return self.DELAYED+str(delay)+self.SEP+name

    def _promise_queue_name(self, epoch_seconds ):
        return self.PROMISES + str(int(epoch_seconds))
        

    @staticmethod
    def _delay_as_int(delay):
        return 0 if delay is None else int(delay)

    def _coerce_sources(self, source:str=None, sources:Optional[NameList]=None, delay=None, delays:Optional[DelayList]=None):
        """ Change name of source to accomodate delay """
        sources    = sources or [ source ]
        delays     = delays  or [ delay ]
        if len(sources)==1 and len(delays)>1:
            sources = [ sources[0] for _ in delays ]
        if len(sources)>1 and len(delays)==1:
            delays = [ delays[0] for _ in sources ]
        assert len(delays)==len(sources)
        delays = [ self._delay_as_int(delay) for delay in delays ]
        # Delays must be valid
        valid  = [ d in [0]+self.DELAY_SECONDS for d in delays ]
        valid_delays  = [ d for d,v in zip(delays,valid)  if v ]
        valid_sources = [ s for s,v in zip(sources,valid) if v ]
        augmented_sources = [ source if delay==0 else self.DELAYED+str(delay)+self.SEP+source for source, delay in zip(valid_sources, valid_delays) ]
        return augmented_sources

# --------------------------------------------------------------------------
#            Implementation  (delete)
# --------------------------------------------------------------------------

    def _delete_implementation(self, name=None, write_key=None, names: Optional[NameList] = None,
                               write_keys: Optional[KeyList] = None):
        """ Permissioned delete """
        names = names or [name]
        self.assert_not_in_reserved_namespace(names)
        write_keys = write_keys or [write_key for _ in names]
        are_valid = self._mauthorize(names, write_keys)

        authorized_kill_list = [name for (name, is_valid_write_key) in zip(names, are_valid) if is_valid_write_key]
        if authorized_kill_list:
            return self._delete(*authorized_kill_list)
        else:
            return 0

    def _sample_owners_name(self, delay):
        return self.OWNERS + self.SAMPLES + str(delay) + self.SEP

    def _delete(self, names, *args):
        """ Remove data, subscriptions, messages, ownership, history, delays, links """
        # TODO: Combine 1+2 into one call to reduce communication
        names = list_or_args(names, args)
        names = [n for n in names if n is not None]

        # (1) List  so we can kill messages in flight
        subs_pipe = self.client.pipeline()
        for name in names:
            subs_pipe.smembers(name=self.SUBSCRIBERS + name)
        for name in names:
            subs_pipe.smembers(name=self.SUBSCRIPTIONS + name)
        res = subs_pipe.execute()
        assert len(res) == 2 * len(names)
        subscribers_res = res[:len(names)]
        subscriptions_res = res[len(names):]

        # (2) Collate backlinks/delays etc
        links_pipe = self.client.pipeline()
        delay_names = list()
        link_names = list()
        sample_names = list()
        prediction_names = list()
        sample_owners_names = list()
        for name in names:
            for delay in self.DELAY_SECONDS:
                delay_name = self.DELAYED + str(delay) + self.SEP + name
                prediction_names.append(self.PREDICTIONS + str(delay) + self.SEP + name)
                sample_names.append(self._samples_name(name=name,delay=delay))
                links_pipe.hgetall(self.LINKS + delay_name)
                delay_names.append(delay_name)
                link_names.append(self.LINKS + delay_name)
                sample_owners_names.append(self._sample_owners_name(delay=delay))

        link_collections = links_pipe.execute()

        # (3) Round up and destroy in one pipeline
        delete_pipe = self.client.pipeline(transaction=False)

        for delay_name, link_collection in zip(delay_names, link_collections):
            for target in list(link_collection.keys()):
                delete_pipe.hdel(self.BACKLINKS + target, delay_name)

        # Remove name from children's list of subscriptions
        for name, subscribers in zip(names, subscribers_res):
            for subscriber in subscribers:
                delete_pipe.srem(self.SUBSCRIPTIONS + subscriber, name)
                recipient_mailbox = self.MESSAGES + subscriber
                if self.INSTANT_RECALL:
                    delete_pipe.hdel(recipient_mailbox, name)

        # Remove name from parent's list of subscribers
        for name, subscriptions in zip(names, subscriptions_res):
            for source in subscriptions:
                delete_pipe.srem(self.SUBSCRIBERS + source, name)

        if len(names) > 3:
            dump(names[:4], 'tmp_names_.json')

        delete_pipe.delete(*link_names)
        delete_pipe.delete(*delay_names)
        delete_pipe.delete(*prediction_names)
        delete_pipe.delete(*sample_names)
        delete_pipe.hdel(self.OWNERSHIP, *names)
        delete_pipe.delete(*[self.MESSAGES + name for name in names])
        delete_pipe.delete(*[self.HISTORY + name for name in names])
        delete_pipe.srem(self.NAMES, *names)
        delete_pipe.delete(*names)
        delete_pipe.delete(*[self.SUBSCRIBERS + name for name in names])
        res = delete_pipe.execute()
        dump({'res': res[-1], 'names': [self.SUBSCRIBERS + name for name in names[:4]]}, 'tmp__.json')
        return res[-2]


     # --------------------------------------------------------------------------
     #            Implementation  (subscribe)
     # --------------------------------------------------------------------------


    def _subscribe_implementation(self, name, write_key,
                                        source=None,    sources:Optional[NameList]=None,
                                        delay:int=None, delays:Optional[DelayList]=None ):
        """ Permissioned subscribe to one or more sources """
        if self._authorize(name=name,write_key=write_key):
            augmented_sources = self._coerce_sources(source=source, sources=sources, delay=delay, delays=delays )
            return self._subscribe( name=name, sources=augmented_sources)
        else:
            return 0

    def _subscribe(self, name, sources ):
        the_pipe = self.client.pipeline()
        for source in sources:
            the_pipe.sadd(self.SUBSCRIBERS+source,name)
        the_pipe.sadd(self.SUBSCRIPTIONS+name,*sources)
        return the_pipe.execute()

    def _subscribers_implementation(self, name, write_key):
        """ List subscribers """
        if self._authorize(name=name,write_key=write_key):
            return list(self.client.smembers(self.SUBSCRIBERS+name))

    def _subscriptions_implementation(self, name, write_key):
        """ List subscriptions """
        if self._authorize(name=name,write_key=write_key):
            return list(self.client.smembers(self.SUBSCRIPTIONS+name))

    def _unsubscribe_implementation(self, name, write_key,
                                        source=None,    sources:Optional[NameList]=None,
                                        delay:int=None, delays:Optional[DelayList]=None ):
        """ Permissioned unsubscribe from one or more sources """
        if self._authorize(name=name,write_key=write_key):
            augmented_sources = self._coerce_sources(source=source, sources=sources, delay=delay, delays=delays )
            pipe = self.client.pipeline()
            pipe = self._unsubscribe( pipe=pipe, name=name, sources=augmented_sources)
            return pipe.execute()
        else:
            return 0

    def _unsubscribe(self, pipe, name, sources ):
        for source in sources:
            pipe.srem(self.SUBSCRIBERS+source, name)
        pipe.srem(self.SUBSCRIPTIONS+name,*sources)
        return pipe

    def _messages_implementation(self, name, write_key):
        if self._authorize(name=name,write_key=write_key):
            return self.client.hgetall( self.MESSAGES+name )




     # --------------------------------------------------------------------------
     #            Implementation  (linking)
     # --------------------------------------------------------------------------


    def _root_name(self,name):
        return name.split(self.SEP)[-1]

    def _link_implementation(self, name, write_key, budget, target=None, targets=None ):
        " Create link to possibly non-existent target(s) "
        if targets is None:
            targets = [ target ]

        root = self._root_name(name)
        if self.exists(root) and (self.DELAYED in name) and not( self.DELAYED in target
               ) and self._authorize(name=root,write_key=write_key):
            link_pipe   = self.client.pipeline()
            edge_weight = 1.0*budget / len(targets)
            for target in targets:
                link_pipe.hset(self.LINKS+name,key=target,value=edge_weight)
                link_pipe.hset(self.BACKLINKS+target,key=name,value=edge_weight)
            link_pipe.execute()
            return budget
        else:
            return 0


    def _unlink_implementation(self, name, write_key, target):
        # Either party can unlink
        if self._authorize(name=name,write_key=write_key) or self._authorize(name=target,write_key=write_key):
            link_pipe   = self.client.pipeline(transaction=True)
            link_pipe.hdel(self.LINKS+name,key=target)
            link_pipe.hdel(self.BACKLINKS+target,key=name)
            return link_pipe.execute()


    def _links_implementation(self, name, write_key):
        if self._authorize(name=name,write_key=write_key):
            return self.client.hgetall(self.LINKS+name)

    def _backlinks_implementation(self, name, write_key):
        if self._authorize(name=name,write_key=write_key):
            return self.client.hgetall(self.BACKLINKS+name)


    # --------------------------------------------------------------------------
    #            Implementation  (Administrative)
    # --------------------------------------------------------------------------

    def admin_promises(self, lookback_seconds=5):
         """ Iterate through task queues populating delays and samples """
         exists_pipe = self.client.pipeline()
         utc_epoch_now = int(time.time())
         candidates =  [ self.PROMISES+str(utc_epoch_now-seconds) for seconds in range(lookback_seconds,-1,-1) ]

         for candidate in candidates:
             exists_pipe.exists(candidate)
         exists = exists_pipe.execute()

         get_pipe = self.client.pipeline()
         promise_collection_names = [ promise for promise,exist in zip(candidates,exists) if exists ]
         for collection_name in promise_collection_names:
             get_pipe.smembers(collection_name)
         collections = get_pipe.execute()
         self.client.delete( *promise_collection_names )  # Immediately delete task list so it isn't done twice ... not that that would
                                                          # be the end of the world
         individual_promises = list( itertools.chain( *collections ) )

         # Sort through promises in reverse time precedence
         # When we set delays, we allow more recent instructions to override less recent ones
         # as there is no point setting the value more than once
         dest_source = dict()
         dest_method = dict()
         copy_sep    = self.SEP + 'copy' + self.SEP
         ticket_sep  = self.SEP + 'ticket' + self.SEP
         for promise in individual_promises:
             if copy_sep in promise:
                 source, destination = promise.split(copy_sep)
                 dest_source[destination] = source
                 dest_method[destination] = 'copy'
             elif ticket_sep in promise:
                 source, destination = promise.split(ticket_sep)
                 dest_source[destination] = source
                 dest_method[destination] = 'ticket'
         sources      = list(dest_source.values())
         destinations = list(dest_source.keys())
         methods      = list(dest_method.values())

         # Get the data
         retrieve_pipe = self.client.pipeline()
         for source, destination, method in zip(sources, destinations, methods):
             if method == 'copy':
                 retrieve_pipe.get(source)
             elif method == 'ticket':
                 retrieve_pipe.zrange(name=source,start=0,end=-1,withscores=True)

         source_values = retrieve_pipe.execute()

         # Copy or insert
         move_pipe = self.client.pipeline(transaction=True)
         for value, destination, method in zip(source_values, destinations, methods):
             if method == 'copy':
                 move_pipe.set(name=destination,value=value)
             elif method == 'ticket':
                 if len(value):
                     value_as_dict = dict(value)
                     move_pipe.zadd(name=destination,mapping=value_as_dict)
                     owners  = [ self._ticket_owner(ticket) for ticket in value_as_dict.keys() ]
                     unique_owners = list(set(owners))
                     move_pipe.sadd(self.OWNERS + destination, *unique_owners)
         execut = move_pipe.execute()
         return sum(execut)

    # --------------------------------------------------------------------------
    #            Implementation  (prediction and settlement)
    # --------------------------------------------------------------------------

    def _dirac(self, name, value, write_key):
        x_noise = list(np.random.randn(self.NUM_PREDICTIONS))
        values  = [ value+x for x in x_noise ]
        return self._predict_implementation( name=name, values=values, write_key=write_key )


    def _ticket(self, write_key, k ):
        return str(k).zfill(8)+ self.SEP + write_key

    def _ticket_owner(self, ticket):
        return ticket.split(self.SEP)[1]

    def _predict_implementation(self, name, values, write_key, delay=None, delays=None):
        """ Set a sorted set """
        import numpy as np
        if delays is None and delays is None:
            delays = self.DELAY_SECONDS
        elif delays is None:
            delays = [ delay ]
        if self.exists(name) and len(values)==self.NUM_PREDICTIONS and self.is_valid_key(write_key
                ) and all( [ isinstance(v,(int,float) ) for v in values] ) and all (delay in self.DELAY_SECONDS for delay in delays):
            # We set a temporary item that only needs to survive long enough to be inserted into the nano-market
            # after a set period of quarantine. Probabilistic predictions are ephemeral, though they live on in
            # the ordered set of all predictions at a given horizon.
            noise =  np.random.randn(self.NUM_PREDICTIONS).tolist()
            jiggered_values = [v + n*self.NOISE for v, n in zip(values, noise)]
            predictions = dict([(self._ticket(write_key=write_key,k=k), v) for k,v in enumerate(jiggered_values)])
            set_and_expire_pipe = self.client.pipeline()

            # Add to collective contemporaneous predictions
            collective_predictions_name = self.PREDICTIONS+write_key+self.SEP+name
            set_and_expire_pipe.zadd(   name=collective_predictions_name, mapping=predictions )  # (0)

            # Create obscure predictions and promise to insert them later, at different times, into different samples
            utc_epoch_now = int(time.time())
            individual_predictions_name = self._promised_name(name)
            set_and_expire_pipe.zadd(name=individual_predictions_name, mapping=predictions)  # (1)
            set_and_expire_pipe.expire(name=individual_predictions_name, time=max(self.DELAY_SECONDS)+self.DELAY_GRACE)   # (2)
            for delay_seconds in delays:
                promise_queue = self.PROMISES + str(utc_epoch_now + delay_seconds)
                promise       = self._ticket_promise(target=name, delay=delay_seconds, predictions_name=individual_predictions_name)
                set_and_expire_pipe.sadd(promise_queue, promise )    # (3::3)
                set_and_expire_pipe.expire(name=promise_queue, time=delay_seconds + self.DELAY_GRACE)  # (4::3)
                set_and_expire_pipe.expire(name=individual_predictions_name, time=delay_seconds + self.DELAY_GRACE)  # (5::3)

            execut = set_and_expire_pipe.execute()
            # Check on executions
            anticipated_execut = [ self.NUM_PREDICTIONS, self.NUM_PREDICTIONS, True ] + [ 1, True, True ]*len(delays)
            success = all( actual==anticipate for actual, anticipate in zip(execut, anticipated_execut) )
            return success
        else:
            return 0

    def _ticket_promise(self, target, delay, predictions_name):
        return predictions_name + self.SEP + 'ticket' + self.SEP+ self._samples_name(name=target,delay=delay)

    def _settle(self, name, value ):
        retrieve_pipe = self.client.pipeline()
        for delay in self.DELAY_SECONDS:
            samples_name = self._samples_name(name=name, delay=delay)        # self.SAMPLES + str(delay) + self.SEP + name
            retrieve_pipe.zcard(samples_name)                                # (0) Total number of entries
            retrieve_pipe.smembers( self._sample_owners_name(delay) )        # (1) List of owners
            for window in self.WINDOWS:                                      # (2,3,...) Tickets inside window
                retrieve_pipe.zrangebyscore( name=samples_name, min=value-window,  max=value+window,  withscores=False)

        # Execute pipeline and re-arrange results
        K = 2 + len(self.WINDOWS)
        retrieved = retrieve_pipe.execute()
        pools            = retrieved[0::K]
        assert all( ( isinstance(p, (int,float)) for p in pools ))
        participant_sets = retrieved[1::K]
        assert all( isinstance(s,set) for s in participant_sets )
        selections = list()
        for k in range(len(self.WINDOWS)):
            selections.append( retrieved[2+k::K] )
        assert all( isinstance(s,list) for s in selections )

        # Select winners in neighbourhood, trying hard for at least one
        if any(pools):
            payments = Counter()
            for pool, selections, participant_set in zip( pools, selections, participant_sets ):
                if pool and len(participant_set)>1:
                    # We have a game !
                    game_payments = Counter( dict( (p,-1.0) for p in participant_set ) )

                    # Enlarge window until we have winner ... probably
                    winning_tickets = selections[0]
                    for select in selections[1:]:
                        if len(winning_tickets)==0:
                            winning_tickets = select

                    if len(winning_tickets) == 0:
                        carryover = Counter({self.JACKPOT:1.0*pool/self.NUM_PREDICTIONS})
                        game_payments.update(carryover)
                    else:
                        winners  = [ self._ticket_owner(ticket) for ticket in winning_tickets ]
                        reward   = ( 1.0*pool/self.NUM_PREDICTIONS ) / len(winners)   # Could augment this to use kernel or whatever
                        payouts  = Counter( dict( [(w,reward*c) for w,c in Counter(winners).items() ]) )

                        game_payments.update(payouts)
                    assert abs(sum( game_payments.values() ))<0.1, "Leakage in zero sum game"
                    payments.update(game_payments)

            if len(payments):
                pay_pipe = self.client.pipeline()
                for (recipient, amount) in payments.items():
                    pay_pipe.hincrbyfloat( name=self.BALANCES,key=recipient,amount=float(amount) )
                return pay_pipe.execute()
        return 0

    # --------------------------------------------------------------------------
    #            Implementation  (getters)
    # --------------------------------------------------------------------------

    def _get_balance_implementation(self, write_key=None, write_keys=None, aggregate=True):
        write_keys = write_keys or [ write_key ]
        balances   = self.client.hmget( self.BALANCES, *write_keys )
        fixed_balances = [ float( b or "0") for b in balances ]
        return np.nansum( fixed_balances ) if aggregate else fixed_balances

    def _get_lagged_implementation(self, name, start=0, end=None, count=100, with_times=False, to_float=True):
        count = count or self.LAGGED_LEN
        end = end or start + count
        get_pipe = self.client.pipeline()
        get_pipe.lrange(name=self.LAGGED + name, start=start, end=end)
        if with_times:
            get_pipe.lrange(name=self.LAGGED_TIMES + name, start=start, end=end)
        res = get_pipe.execute()
        values = RedizConventions.to_float(res[0]) if to_float else res[0]
        if with_times:
            times = RedizConventions.to_float(res[1] if to_float else res[1])
        return zip(times, values) if with_times else values

    def _get_delayed_implementation(self, names, delay=None, delays=None, to_float=True):
        """ Get delayed values from one or more names """
        singular = delays is None
        delays = delays or [delay for _ in names]
        names = [self.DELAYED + str(delay) + self.SEP + name for name, delay in zip(names, delays)]
        delayed = self._get_implementation(names=names)
        if to_float:
            delayed = RedizConventions.to_float( delayed )
        return delayed[0] if singular else delayed

    def _get_implementation(self, name: Optional[str] = None,
                            names: Optional[NameList] = None, cast=None, **nuissance):
        """ Retrieve value(s). No permission required. """
        plural = names is not None
        names = names or [name]
        res = self._pipelined_get(names=names)
        return res if plural else res[0]

    def _get_history_implementation(self, name, min, max, count, populate, drop_expired ):
        """ Retrieve history, optionally replacing pointers with actual values  """
        history = self.client.xrevrange(name=self.HISTORY+name, min=min, max=max, count=count )
        if populate:
            has_pointers = any( self.POINTER in record for record in history )
            if has_pointers and populate:
                pointers = dict()
                for k, record in enumerate(history):
                    if self.POINTER in record:
                        pointer = record[self.POINTER]
                        pointers[k] = record[self.POINTER]

                values  = self.client.mget( pointers )
                expired = list()
                for k, record in enumerate(history):
                    if k in pointers:
                        if values is not None:
                            fields = RedizConventions.to_record(values[k])
                            record.update(fields)
                            expired.append(k)

                if drop_expired:
                    history = [ h for j,h in enumerate(history) if not j in expired ]
        return history

    def _obscure_ticket(self, ticket):
        parts = ticket.split(self.SEP)
        return parts[0]+self.SEP+self.hash(parts[1])

    def _samples_name(self, name, delay):
        return self.SAMPLES + str(delay) + self.SEP + name

    def _get_samples_implementation(self, name, delay=None, delays=None):
        """ Get all tickets but hash the write_keys """
        singular = delays is None
        delays   = delays or [delay]
        samples  = [self._samples_name(name=name,delay=delay) for delay in delays ]
        pipe = self.client.pipeline()
        for sample in samples:
            pipe.zrange(name=sample, start=0, end=-1, withscores=True )
        private_samples = pipe.execute()
        obscured = list()
        for sample in private_samples:
            obscure = dict( [ (self._obscure_ticket(ticket),v) for (ticket,v) in sample ] )
            obscured.append(obscure)
        return obscured[0] if singular else obscured

