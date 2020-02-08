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
        self.COPY_SEP = self.SEP+"copy"+self.SEP
        self.PREDICTION_SEP = self.SEP+"prediction"+self.SEP

        # Rediz instance. Expects host, password, port   If not supplied it may use fakeredis
        self.client         = self.make_redis_client(**kwargs)                 # Real or mock redis client

        # Implementation details: private reserved redis keys and prefixes.
        self._obscurity     = ( kwargs.get("obscurity") or "09909-OBSCURE-c94748" ) + self.SEP
        self._RESERVE        = self._obscurity + "reserve"                     # Reserve of credits fed by rare cases when all models miss wildly
        self._OWNERSHIP      = self._obscurity + "ownership"                   # Official map from name to write_key
        self._NAMES          = self._obscurity + "names"                       # Redundant set of all names (needed for random sampling when collecting garbage)
        self._PROMISES       = self._obscurity + "promises" + self.SEP         # Prefixes queues of operations that are indexed by epoch second
        self._POINTER        = self._obscurity + "pointer"                     # A convention used in history stream
        self._BALANCES       = self._obscurity + "balance" + self.SEP          # Hash of all balances attributed to write_keys
        self._PREDICTIONS    = self._obscurity + "predictions" + self.SEP      # Prefix to a listing of contemporaneous predictions by horizon. Must be private as this contains write_keys
        self._OWNERS         = "owners" + self.SEP                             # Prefix to a redundant listing of contemporaneous prediction owners by horizon. Must be private as this contains write_keys
        self._SAMPLES        = self._obscurity + "samples" + self.SEP          # Prefix to delayed predictions by horizon. Contain write_keys !
        self._PROMISED       = "promised" + self.SEP                           # Prefixes temporary values referenced by the promise queue

        # User facing conventions: transparent use of prefixing
        self.ERRORS         = "errors" + self.SEP
        self.DELAYED        = "delayed"+self.SEP
        self.LINKS          = "links"+self.SEP
        self.BACKLINKS      = "backlinks"+self.SEP
        self.MESSAGES       = "messages"+self.SEP
        self.HISTORY        = "history"+self.SEP
        self.HISTORY_LEN    = int( kwargs.get("history_len") or 1000 )
        self.LAGGED_VALUES  = "lagged_values" + self.SEP
        self.LAGGED_TIMES   = "lagged_times" + self.SEP
        self.LAGGED_LEN     = int( kwargs.get("lagged_len") or 10000 )
        self.SUBSCRIBERS    = "subscribers"+self.SEP
        self.SUBSCRIPTIONS  = "subscriptions"+self.SEP

        # User transparent temporal config
        self.DELAYS           = kwargs.get("delay_seconds") or [1, 5, 60, 10 * 60, 30 * 60]
        self.ERROR_TTL        = int( kwargs.get('error_ttl') or 60 * 5)      # Number of seconds that set execution error logs are persisted
        self.ERROR_LIMIT      = int(kwargs.get('error_limit') or 1000)       # Number of error messages to keep per write key
        self.NUM_PREDICTIONS  = int(kwargs.get("num_predictions") or 1000)   # Number of scenerios in a prediction batch
        self.NOISE            = 1.0 / self.NUM_PREDICTIONS  # Tie-breaking / smoothing noise added to predictions

        # Other implementation config
        self._DELAY_GRACE       = int(kwargs.get("delay_grace") or 60)      # Seconds beyond the schedule time when promise data expires
        self._DEFAULT_MODEL_STD = 1.0                                       # Noise added for self-prediction
        self._WINDOWS           = [1e-4, 1e-3]                              # Sizes of neighbourhoods around truth used in countback ... don't make too big or it hits performance
        self._INSTANT_RECALL    = kwargs.get("instant_recall") or False     # Delete messages already sent when sender is deleted?
        self._MAX_TTL           = 60*60                                     # Maximum TTL, useful for testing

    # --------------------------------------------------------------------------
    #            Public (api/web) interface - getters
    # --------------------------------------------------------------------------

    def card(self):
        return self.client.scard(self._NAMES)

    def exists(self, name ):
        return self.client.sismember(name=self._NAMES,value=name)

    def get(self, name, as_json=False, **kwargs ):
        """ Unified getter expecting prefixed name - used by web application """
        parts = name.split(self.SEP)
        data  = None
        kwargs.update({"as_json":as_json})
        if len(parts)==1:
            data =  self._get_implementation(name=name,**kwargs )
        elif len(parts)==2:
            if parts[-2] == self.BACKLINKS:
                data = self.get_backlinks(name=parts[-1] )
            elif parts[-2] == self.SUBSCRIPTIONS:
                data = self.get_subscriptions(name=parts[-1] )
            elif parts[-2] == self.SUBSCRIBERS:
                data = self.get_subscribers(name=parts[-1] )
            elif parts[-2] == self.LAGGED_VALUES:
                data =  self.get_lagged(name=parts[-1], **kwargs  )
            elif parts[-2] == self.ERRORS:
                data = self.get_errors(write_key=parts[-1], **kwargs)
            elif parts[-2] == self.HISTORY:
                data =  self.get_history(name=parts[-1], **kwargs)
        elif len(parts)==3:
            if parts[-3] == self.DELAYED:
                data = self.get_delayed(name=parts[-1], delay=int(parts[-2]), to_float=True)
            elif parts[-3] == self._PREDICTIONS:
                data =  self.get_predictions(name=parts[-1],delay=int(parts[-2]) )
            elif parts[-3] == self._SAMPLES:
                data =  self.get_samples(name=parts[-1], delay=int(parts[-2]) )
            elif parts[-3] == self.LINKS:
                data =  self.get_links(name=parts[-1], delay=int(parts[-2])  )
        elif len(parts)==4:
            pass

        if isinstance(data,set):
            data = list(set)
        return json.dumps(data) if as_json else data

    def mget(self, names:NameList, *args):
        names = list_or_args(names,args)
        return self._get_implementation( names=names )

    def get_samples(self, name, delay=None, delays=None):
        return self._get_samples_implementation(name=name, delay=delay, delays=delays)

    def get_predictions(self, name, delay=None, delays=None):
        return self._get_predictions_implementation(name=name, delay=delay, delays=delays)

    def get_reserve(self):
        return float(self.client.hget(self._BALANCES, self._RESERVE) or 0)

    def get_delayed(self, name, delay=None, delays=None, to_float=True):
        return self._get_delayed_implementation( name=name, delay=delay, delays=delays, to_float=to_float)

    def get_lagged(self, name, start=0, end=None, count=None, to_float=True ):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=True, with_times=True, to_float=to_float)

    def get_lagged_values(self, name, start=0, end=None, count=None, to_float=True):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=True, with_times=False, to_float=to_float)

    def get_lagged_times(self, name, start=0, end=None, count=None, to_float=True):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=False, with_times=True, to_float=to_float)

    def get_balance(self, write_key ):
        return self._get_balance_implementation(write_key=write_key)

    def mget_balance(self, write_keys, aggregate=True):
        return self._get_balance_implementation(write_keys=write_keys, aggregate=aggregate)

    def get_history(self, name, max='+', min='-', count=None, populate=True, drop_expired=True ):
        return self._get_history_implementation( name=name, max=max, min=min, count=None, populate=True, drop_expired=True )

    def get_subscriptions(self, name ):
        return self._get_subscriptions_implementation(name=name)

    def get_subscribers(self, name ):
        return self._get_subscribers_implementation(name=name)

    def get_errors(self, write_key, start=0, end=-1):
        return self.client.lrange(name=self._errors_name(write_key=write_key), start=start, end=end)

    def get_links(self, name, delay=None, delays=None ):
        assert not self.SEP in name, "Intent is to provide delay variable"
        return self._get_links_implementation(name=name, delay=delay, delays=delays )

    def get_backlinks(self, name ):
        return self._get_backlinks_implementation(name=name )

    # --------------------------------------------------------------------------
    #            Permissioned get
    # --------------------------------------------------------------------------

    def get_messages(self,name, write_key):
        if self._authorize(name=name, write_key=write_key):
            return self._get_messages_implementation(name=name,write_key=write_key)


    # --------------------------------------------------------------------------
    #           Public conventions (names and places )
    # --------------------------------------------------------------------------

    def derived_names(self, name):
        """ Summary of data and links  """
        references = dict()
        for method_name, method in self._nullary_methods().items():
            item = {method_name: method(name)}
            references.update(item)
        for method_name, method in self._delay_methods().items():
            for delay in self.DELAYS:
                item = {method_name + self.SEP + str(delay): method(name=name, delay=delay)}
                references.update(item)
        return references

    def _private_derived_names(self, name):
        references = dict()
        for method_name, method in self._private_delay_methods().items():
            for delay in self.DELAYS:
                item = {method_name + self.SEP + str(delay): method(name=name, delay=delay)}
                references.update(item)
        return references

    def _nullary_methods(self):
        return {"name":self._identity,
                "lagged":self.lagged_values_name,
                "lagged_times": self.lagged_times_name,
                "backlinks": self.backlinks_name,
                "subscribers":self.subscribers_name,
                "subscriptions":self.subscriptions_name,
                "history":self.history_name,
                "messages":self.messages_name}

    def _delay_methods(self):
        return {"delayed":self.delayed_name,
                "links": self.links_name,
                "participants":self._sample_owners_name}

    def _private_delay_methods(self):
        return {"participants": self._sample_owners_name,
                "predictions": self._predictions_name,
                "samples": self._samples_name
                }


    def _identity(self, name):
        return name

    def delayed_name(self, name, delay):
        return self.DELAYED + str(delay) + self.SEP + name

    def messages_name(self, name):
        return self.MESSAGES + name

    def history_name(self, name):
        return self.HISTORY + name

    def lagged_values_name(self, name):
        return self.LAGGED_VALUES + name

    def lagged_times_name(self, name):
        return self.LAGGED_TIMES + name

    def links_name(self,name,delay):
        return self.LINKS + str(delay) + self.SEP + name

    def backlinks_name(self, name):
        return self.BACKLINKS + name

    def subscribers_name(self, name):
        return self.SUBSCRIBERS + name

    def subscriptions_name(self, name):
        return self.SUBSCRIPTIONS + name

    # --------------------------------------------------------------------------
    #           Private conventions (names, places, formats )
    # --------------------------------------------------------------------------

    def _ownership_name(self):
        return self._OWNERSHIP

    def _promised_name(self, name):
        return self._PROMISED + self.random_key()[:8] + self.SEP + name[:14]

    def _copy_promise(self, source, destination):
        return source + self.COPY_SEP + destination

    def _promise_queue_name(self, epoch_seconds):
        return self._PROMISES + str(int(epoch_seconds))

    def _sample_owners_name(self, name, delay):
        return self._OWNERS + self._SAMPLES + str(delay) + self.SEP + name

    def _predictions_name(self, name, delay):
        return self._PREDICTIONS + str(delay) + self.SEP + name

    def _samples_name(self, name, delay):
        if name is None or delay is None:
            x = 43
            dumfounded = x
            raise Exception('groan')
        else:
            try:
                return self._SAMPLES + str(delay) + self.SEP + name
            except TypeError:
                dumbfounded = True
                raise Exception('urgh')

    def _format_scenario(self, write_key, k):
        """ A "ticket" indexed by write_key and an index from 0 to self.NUM_PREDiCTIONS-1 """
        return str(k).zfill(8)+ self.SEP + write_key

    def _make_scenario_obscure(self, ticket):
        """ Change write_key to a hash of write_key """
        parts = ticket.split(self.SEP)
        return parts[0]+self.SEP+self.hash(parts[1])

    def _scenario_owner(self, scenario):
        return scenario.split(self.SEP)[1]

    def _prediction_promise(self, target, delay, predictions_name):
        """ Format for a promise that sits in a promise queue waiting to be inserted into samples::1::name, for instance """
        return predictions_name + self.PREDICTION_SEP + self._samples_name(name=target, delay=delay)

    def _interpret_delay(self, delay_name ):
        assert self.DELAYED in delay_name
        parts = delay_name.split(self.SEP)
        root  = parts[-1]
        delay = int( parts[-2] )
        return root, delay

    # --------------------------------------------------------------------------
    #           Private getters
    # --------------------------------------------------------------------------

    def _get_sample_owners(self,name,delay):
        return list( self.client.smembers( self._sample_owners_name(name=name,delay=delay) ) )

    # --------------------------------------------------------------------------
    #            Public interface  (set/delete)
    # --------------------------------------------------------------------------

    def set( self, name, value, write_key ):
        return self._set_implementation(name=name, value=value, write_key=write_key, return_args=None, budget=1 )

    def mset(self,names:NameList, values:ValueList, write_keys:KeyList):
        return self._set_implementation(names=names, values=values, write_keys=write_keys, return_args=None, budget=1000 )

    def delete(self, name, write_key):
        return self._permissioned_mdelete(name=name, write_key=write_key)

    def mdelete(self, names, write_key:Optional[str]=None, write_keys:Optional[KeyList]=None):
        return self._permissioned_mdelete(names=names, write_key=write_key, write_keys=write_keys)

    def predict(self, name, values, write_key ):
        return self._predict_implementation( name, values, write_key )


    # Public interface: Subscription

    def subscribe(self, name, write_key, source ):
        """ Permissioned subscribe """
        return self._permissioned_subscribe_implementation( name=name, write_key=write_key, source=source )

    def msubscribe(self, name, write_key, sources ):
        """ Permissioned subscribe to multiple sources """
        return self._permissioned_subscribe_implementation(name=name, write_key=write_key, sources=sources )

    def unsubscribe(self, name, write_key, source ):
        return self._permissioned_unsubscribe_implementation(name=name, write_key=write_key, source=source)

    def munsubscribe(self, name, write_key, sources, delays=None):
        return self._permissioned_unsubscribe_implementation(name=name, write_key=write_key, sources=sources)

    def messages(self, name, write_key):
        """ Use key to open the mailbox """
        return self._get_messages_implementation(name=name, write_key=write_key)

    # Public interface: Linking

    def link(self, name, write_key, delay, target=None, targets=None ):
        """ Link from a delay to one or more targets """
        return self._permissioned_link_implementation(name=name, write_key=write_key, delay=delay, target=target, targets=targets)

    def unlink(self, name, delay, write_key, target):
        """ Permissioned removal of link (either party can do this) """
        return self._unlink_implementation(name=name, delay=delay, write_key=write_key, target=target )


    # --------------------------------------------------------------------------
    #            Implementation  (client init)
    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------
    #            Implementation  (permissions)
    # --------------------------------------------------------------------------

    def _authorize(self,name,write_key):
        return write_key==self._authority(name=name)

    def _mauthorize(self,names,write_keys):
        authority = self._mauthority(names)
        assert len(names)==len(write_keys)
        comparison = [ k==k1 for (k,k1) in zip( write_keys, authority ) ]
        return comparison

    def _authority(self,name):
        root = self._root_name(name)
        return self.client.hget(self._ownership_name(),root)

    def _mauthority(self,names, *args):
        names = list_or_args(names,args)
        return self.client.hmget(self._ownership_name(),*names)

    # --------------------------------------------------------------------------
    #            Economic model for data storage (set)
    # --------------------------------------------------------------------------

    @staticmethod
    def _cost_based_ttl(values, multiplicity: int = 1, budget: int = 1):
        # Assign a time to live based on random sampling of the size of values stored.
        # Because this can be abused, it is private for now.
        #
        # However as a rough guide:
        #      A vector of 100 floats lasts a week.
        #      A vector of 1000 floats lasts a day.
        REPLICATION = 3.  # History, Lagged
        DOLLAR = 10000.   # Credits per dollar
        COST_PER_MONTH_10MB = 1. * DOLLAR
        COST_PER_MONTH_1b = COST_PER_MONTH_10MB / (10 * 1000 * 1000)
        SECONDS_PER_DAY = 60. * 60. * 24.
        SECONDS_PER_MONTH = SECONDS_PER_DAY * 30.
        FIXED_COST_bytes = 100  # Overhead
        MAX_TTL_SECONDS = int(SECONDS_PER_DAY * 7)

        if len(values):
            if len(values) < 10:
                value_sample = values
            else:
                value_sample = random.sample(values, 10)
            num_bytes = max((sys.getsizeof(value) for value in values))

            credits_per_month = multiplicity * REPLICATION * (num_bytes + FIXED_COST_bytes) * COST_PER_MONTH_1b
            ttl_seconds = int(math.ceil(SECONDS_PER_MONTH / credits_per_month))
            ttl_seconds = budget * ttl_seconds
            ttl_seconds = min(ttl_seconds, MAX_TTL_SECONDS)
            return ttl_seconds
        return 1

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

        # Encode dict into JSON and crash if value is not JSON serializable
        values = [ v if isinstance(v,(int,float,str)) else json.dumps(v) for v in values ]

        # Execute and create temporary logs
        execution_log = self._pipelined_set( names=names,values=values, write_keys=write_keys, budget=budget )

        if len(values)==1 and isinstance( values[0], (int,float) ):
            # Seed the nano-markets and settle the existing ones.
            self._baseline_prediction(name=name, value=values[0], write_key=write_keys[0])
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

        ttl  = self._cost_based_ttl(budget=budget, multiplicity=multiplicity, values=values)
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
                exists_pipe.hexists(name=self._ownership_name(),key=name)
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

        # Return those we are yet to get to because they are not new
        names          = [ n for n,ndx in zip(names, ndxs)       if ndx in ignored_ndxs ]
        values         = [ v for v,ndx in zip(values, ndxs)      if ndx in ignored_ndxs ]
        write_keys     = [ w for w,ndx in zip(write_keys, ndxs)  if ndx in ignored_ndxs ]
        return executed, rejected, ignored_ndxs, names , values, write_keys

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
                    error_pipe.lpush(self._errors_name(write_key=write_key), json.dumps(auth_message))
                    error_pipe.expire(self._errors_name(write_key=write_key), self.ERROR_TTL)
                    error_pipe.ltrim(name=self._errors_name(write_key=write_key),start=0,end=self.ERROR_LIMIT)
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
                mailbox_name = self.messages_name(subscriber)
                propagate_pipe.hset(name=mailbox_name,key=sender_name, value=value)
                executed.append({"mailbox_name":mailbox_name,"sender":sender_name,"value":value})

        if len(executed):
            propagation_results = Rediz.pipe_results_grouper( results = propagate_pipe.execute(), n=len(executed) ) # Overkill while there is 1 op
            for intent, res in zip(executed,propagation_results):
                intent.update({"result":res})

        return executed

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
        pipe.hset(name=self._ownership_name(),key=name,value=write_key)  # Establish ownership
        pipe.sadd(self._NAMES, name)                                # Need this for random access
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


    def _modify_page(self, pipe,ndx,name,value,ttl):
        """ Create pipelined operations for save, buffer, history etc """

        # (1) Set the actual value ... which will soon be overwritten ... and a randomly generated copy
        pipe.set(name=name,value=value,ex=ttl)
        name_of_copy = self._promised_name(name)
        HISTORY_TTL = min(max(2 * 60 * 60, ttl), 60 * 60 * 24)
        pipe.set(name=name_of_copy, value=value, ex=HISTORY_TTL)

        # (2) Write history log stream and buffers which may or may not include value field(s)
        if self._streams_support():
            if self.is_small_value(value):
                fields = RedizConventions.to_record(value)
            else:
                fields = {self._POINTER: name_of_copy}
            pipe.xadd(name=self.HISTORY + name, fields=fields)
            pipe.xtrim(name=self.HISTORY + name, maxlen=self.HISTORY_LEN)

        # (3) For scalar and vector only, write to simple buffer lists
        if self.is_scalar_value(value) or self.is_vector_value(value) and self.is_small_value(value):
            t = time.time()
            pipe.lpush(self.lagged_values_name(name), value)
            pipe.lpush(self.lagged_times_name(name), t)
            pipe.ltrim(name=self.LAGGED_VALUES + name, start=0, end=self.LAGGED_LEN)

        # (4) Construct delay promises
        utc_epoch_now = int(time.time())
        for delay in self.DELAYS:
            queue       = self._promise_queue_name( utc_epoch_now+delay )            # self.PROMISES+str(utc_epoch_now+delay)
            destination = self.delayed_name(name=name, delay=delay)               # self.DELAYED+str(delay_seconds)+self.SEP+name
            promise     = self._copy_promise(source=name_of_copy, destination=destination)
            pipe.sadd( queue, promise )
            pipe.expire(name=queue, time=delay+self._DELAY_GRACE)

        # (5) Execution log
        intent = {"ndx":ndx,"name":name,"value":value,"ttl":ttl,
                  "new":False,"obscure":False,"copy":name_of_copy}

        return pipe, intent


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
        valid  = [d in [0] + self.DELAYS for d in delays]
        valid_delays  = [ d for d,v in zip(delays,valid)  if v ]
        valid_sources = [ s for s,v in zip(sources,valid) if v ]
        augmented_sources = [source if delay==0 else self.delayed_name(name=source, delay=delay) for source, delay in zip(valid_sources, valid_delays)]
        return augmented_sources

# --------------------------------------------------------------------------
#            Implementation  (delete)
# --------------------------------------------------------------------------

    def _permissioned_mdelete(self, name=None, write_key=None, names: Optional[NameList] = None,
                              write_keys: Optional[KeyList] = None):
        """ Permissioned delete """
        names = names or [name]
        self.assert_not_in_reserved_namespace(names)
        write_keys = write_keys or [write_key for _ in names]
        are_valid = self._mauthorize(names, write_keys)

        authorized_kill_list = [name for (name, is_valid_write_key) in zip(names, are_valid) if is_valid_write_key]
        if authorized_kill_list:
            return self._delete_implementation(*authorized_kill_list)
        else:
            return 0


    def _delete_implementation(self, names, *args):
        """ Removes all traces of name """

        names = list_or_args(names, args)
        names = [n for n in names if n is not None]

        # (a) Gather and assemble stream "edges"  (links, backlinks, subscribers, subscriptions)
        info_pipe = self.client.pipeline()
        for name in names:
            info_pipe.smembers(self.subscribers_name(name))
        for name in names:
            info_pipe.smembers(self.subscriptions_name(name))
        for name in names:
            info_pipe.hgetall(self.backlinks_name(name))
        links_ndx = dict( [ (k,dict()) for k in range(len(names)) ] )
        for name_ndx, name in enumerate(names):
            for delay_ndx, delay in enumerate(self.DELAYS):
                links_ndx[name_ndx][delay_ndx] = len(info_pipe)
                info_pipe.hgetall(self.links_name(name=name,delay=delay))

        info_exec = info_pipe.execute()
        assert len(info_exec) == 3 * len(names) + len(names)*len(self.DELAYS)
        subscribers_res   = info_exec[:len(names)]
        subscriptions_res = info_exec[len(names):2*len(names)]
        backlinks_res     = info_exec[2*len(names):]

        # (b)   Second call will do all remaining cleanup
        delete_pipe = self.client.pipeline(transaction=False)

        # (b-1) Force backlinkers to unlink
        for name, backlinks in zip(names, backlinks_res):
            for backlink in list(backlinks.keys()):
                root, delay = self._interpret_delay(backlink)
                delete_pipe = self._unlink_pipe(pipe=delete_pipe, name=root, delay=int(delay), target=name )

        # (b-2) Force subscribers to unsubscribe
        for name, subscribers in zip(names, subscribers_res):
            for subscriber in subscribers:
                delete_pipe = self._unsubscribe_pipe(pipe=delete_pipe, name=subscriber, source=name)

        # (b-3) Unsubscribe gracefully
        for name, sources in zip(names, subscriptions_res):
            delete_pipe = self._unsubscribe_pipe(pipe=delete_pipe, name=name, sources=sources)

        # (b-4) Unlink gracefully
        for name_ndx, name in enumerate(names):
            for delay_ndx, delay in enumerate(self.DELAYS):
                link_ndx = links_ndx[name_ndx][delay_ndx]
                targets = list(info_exec[ link_ndx ].keys())
                if targets:
                    for target in targets:
                        delete_pipe = self._unlink_pipe(pipe=delete_pipe, name=name, delay=delay, target=target )

        # (b-5) Then discard derived ... delete can be slow so we expire instead
        for name in names:
            derived_names = list(self.derived_names(name).values()) + list(self._private_derived_names(name).values())
            for derived_name in derived_names:
                t = random.choice([0,1,20,60,100])
                delete_pipe.expire(name=derived_name,time=t)

        # (b-6) And de-register the name
        delete_pipe.srem(self._NAMES,*names)
        delete_pipe.hdel(self._ownership_name(),*names)

        del_exec = delete_pipe.execute()
        return sum( ( 1 for r in del_exec if r ) )

     # --------------------------------------------------------------------------
     #            Implementation  (subscribe)
     # --------------------------------------------------------------------------

    def _permissioned_subscribe_implementation(self, name, write_key, source=None, sources:Optional[NameList]=None):
        """ Permissioned subscribe to one or more sources """
        if self._authorize(name=name,write_key=write_key):
            return self._subscribe_implementation(name=name, source=source, sources=sources )

    def _subscribe_implementation(self, name, source=None, sources=None ):
        if source or sources:
            sources = sources or [ source ]
            the_pipe = self.client.pipeline()
            for _source in sources:
                the_pipe.sadd( self.subscribers_name( _source ),name)
            the_pipe.sadd(self.subscriptions_name(name),*sources)
            exec = the_pipe.execute()
            return sum(exec)/2
        else:
            return 0

    def _unsubscribe_pipe(self, pipe, name, source=None, sources=None ):
        if source or sources:
            sources = sources or [source]
            for _source in sources:
                if _source is not None:
                    pipe.srem(self.subscribers_name(_source), name)
            if self._INSTANT_RECALL:
                pipe.hdel(self.messages_name(name), sources)
            pipe.srem(self.subscriptions_name(name), *sources)
        return pipe

    def _permissioned_unsubscribe_implementation(self, name, write_key, source=None, sources:Optional[NameList]=None):
        """ Permissioned unsubscribe from one or more sources """
        if self._authorize(name=name,write_key=write_key):
            pipe = self.client.pipeline()
            pipe = self._unsubscribe_pipe(pipe=pipe, name=name, source=source, sources=sources )
            exec = pipe.execute()
            return sum(exec)
        else:
            return 0

    def _get_messages_implementation(self, name, write_key ):
        if self._authorize(name=name,write_key=write_key):
            return self.client.hgetall( self.MESSAGES+name )

     # --------------------------------------------------------------------------
     #            Implementation  (linking)
     # --------------------------------------------------------------------------

    def _root_name(self,name):
        return name.split(self.SEP)[-1]

    def _permissioned_link_implementation(self, name, write_key, delay, target=None, targets=None):
        " Create link to possibly non-existent target(s) "
        # TODO: Optimize with a beg for forgiveness patten
        if targets is None:
            targets = [ target ]
        root = self._root_name(name)
        assert root==name," Supply root name and a delay "
        target_root = self._root_name(target)
        assert target==target_root
        if self._authorize(name=root,write_key=write_key):
            link_pipe   = self.client.pipeline()
            link_pipe.exists(*targets)
            edge_weight = 1.0   # May change in the future
            for target in targets:
                link_pipe.hset(self.links_name(name=name,delay=delay),key=target,value=edge_weight)
                link_pipe.hset(self.backlinks_name(name=target),key=self.delayed_name(name=name,delay=delay),value=edge_weight)
            exec = link_pipe.execute()
            return sum(exec)/2
        else:
            return 0


    def _unlink_implementation(self, name, delay, write_key, target):
        # Either party can unlink
        if self._authorize(name=name,write_key=write_key) or self._authorize(name=target,write_key=write_key):
            pipe   = self.client.pipeline(transaction=True)
            pipe   = self._unlink_pipe( pipe=pipe, name=name, delay=delay, target=target )
            exec   = pipe.execute()
            return exec

    def _unlink_pipe(self, pipe, name, delay, target ):
        pipe.hdel(self.links_name(name,delay), target)
        pipe.hdel(self.backlinks_name(target), self.delayed_name(name=name,delay=delay))
        return pipe

    # --------------------------------------------------------------------------
    #      Implementation  (Admministrative - garbage collection )
    # --------------------------------------------------------------------------

    def admin_garbage_collection(self, fraction=0.01 ):
        """ Randomized search and destroy for expired data """
        num_keys     = self.client.scard(self._NAMES)
        num_survey   = min( 100, max( 20, int( fraction*num_keys ) ) )
        orphans      = self._randomly_find_orphans( num=num_survey )
        if orphans is not None:
            self._delete_implementation(*orphans)
            return len(orphans)
        else:
            return 0


    def _randomly_find_orphans(self,num=1000):
        NAMES = self._NAMES
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

    # --------------------------------------------------------------------------
    #            Implementation  (Administrative - promises)
    # --------------------------------------------------------------------------

    def admin_promises(self ):
         """ Iterate through task queues populating delays and samples """

         # Find recent promise queues that exist
         exists_pipe   = self.client.pipeline()
         utc_epoch_now = int(time.time())
         candidates    =  [self._promise_queue_name( epoch_seconds=utc_epoch_now-seconds ) for seconds in range(self._DELAY_GRACE, -1, -1)]
         for candidate in candidates:
             exists_pipe.exists(candidate)
         exists = exists_pipe.execute()

         # If they exist get the members
         get_pipe = self.client.pipeline()
         promise_collection_names = [ promise for promise,exist in zip(candidates,exists) if exists ]
         for collection_name in promise_collection_names:
             get_pipe.smembers(collection_name)
         collections = get_pipe.execute()
         self.client.delete( *promise_collection_names )  # Immediately delete task list so it isn't done twice ... not that that would
                                                          # be the end of the world
         individual_promises = list( itertools.chain( *collections ) )

         # Sort through promises in reverse time precedence
         # In particular, we allow more recent copy instructions to override less recent ones
         dest_source = dict()
         dest_method = dict()
         for promise in individual_promises:
             if self.COPY_SEP in promise:
                 source, destination = promise.split(self.COPY_SEP)
                 dest_source[destination] = source
                 dest_method[destination] = 'copy'
             elif self.PREDICTION_SEP in promise:
                 source, destination = promise.split(self.PREDICTION_SEP)
                 dest_source[destination] = source
                 dest_method[destination] = 'predict'
             else:
                 raise Exception("invalid promise")

         sources      = list(dest_source.values())
         destinations = list(dest_source.keys())
         methods      = list(dest_method.values())

         # Interpret the promises as source / destination references and get the source values
         retrieve_pipe = self.client.pipeline()
         for source, destination, method in zip(sources, destinations, methods):
             if method == 'copy':
                 retrieve_pipe.get(source)
             elif method == 'predict':
                 retrieve_pipe.zrange(name=source,start=0,end=-1,withscores=True)
         source_values = retrieve_pipe.execute()

         # Copy delay promises and insert prediction promises
         move_pipe = self.client.pipeline(transaction=True)
         for value, destination, method in zip(source_values, destinations, methods):
             if method == 'copy':
                 move_pipe.set(name=destination,value=value)
             elif method == 'predict':
                 if len(value):
                     value_as_dict = dict(value)
                     move_pipe.zadd(name=destination,mapping=value_as_dict)
                     owners  = [self._scenario_owner(ticket) for ticket in value_as_dict.keys()]
                     unique_owners = list(set(owners))
                     move_pipe.sadd(self._OWNERS + destination, *unique_owners)
             else:
                 raise Exception("bug - missing case ")

         execut = move_pipe.execute()

         # Admin log


         return sum(execut)

    # --------------------------------------------------------------------------
    #            Implementation  (prediction and settlement)
    # --------------------------------------------------------------------------

    def _baseline_prediction(self, name, value, write_key):
        """ A low benchmark that is assigned to the stream owner"""
        x_noise = list(np.random.randn(self.NUM_PREDICTIONS))
        values  = [ value+x for x in x_noise ]
        return self._predict_implementation( name=name, values=values, write_key=write_key )

    def _predict_implementation(self, name, values, write_key, delay=None, delays=None):
        """ Supply paths """
        if delays is None and delays is None:
            delays = self.DELAYS
        elif delays is None:
            delays = [ delay ]
        assert name==self._root_name(name)
        if len(values)==self.NUM_PREDICTIONS and self.is_valid_key(write_key
                ) and all( [ isinstance(v,(int,float) ) for v in values] ) and all (delay in self.DELAYS for delay in delays):
            # Jigger predictions
            noise =  np.random.randn(self.NUM_PREDICTIONS).tolist()
            jiggered_values = [v + n*self.NOISE for v, n in zip(values, noise)]
            predictions = dict([(self._format_scenario(write_key=write_key, k=k), v) for k, v in enumerate(jiggered_values)])

            # Open pipeline
            set_and_expire_pipe = self.client.pipeline()

            # Add to collective contemporaneous forward predictions
            for delay in delays:
                collective_predictions_name = self._predictions_name(name, delay)
                set_and_expire_pipe.zadd(   name=collective_predictions_name, mapping=predictions, ch=True )  # (0)

            # Create obscure predictions and promise to insert them later, at different times, into different samples
            utc_epoch_now = int(time.time())
            individual_predictions_name = self._promised_name(name)
            set_and_expire_pipe.zadd(name=individual_predictions_name, mapping=predictions, ch=True)                  # (1)
            set_and_expire_pipe.expire(name=individual_predictions_name, time=max(self.DELAYS) + self._DELAY_GRACE)   # (2)
            for delay_seconds in delays:
                promise_queue = self._promise_queue_name( utc_epoch_now + delay_seconds )
                promise       = self._prediction_promise(target=name, delay=delay_seconds, predictions_name=individual_predictions_name)
                set_and_expire_pipe.sadd(promise_queue, promise )    # (3::3)
                set_and_expire_pipe.expire(name=promise_queue, time=delay_seconds + self._DELAY_GRACE)  # (4::3)
                set_and_expire_pipe.expire(name=individual_predictions_name, time=delay_seconds + self._DELAY_GRACE)  # (5::3)

            # Execute pipeline ... should not fail (!)
            execut = set_and_expire_pipe.execute()
            anticipated_execut = [self.NUM_PREDICTIONS]*len(delays) + [ self.NUM_PREDICTIONS, True ] + [ 1, True, True ]*len(delays)
            success = all( actual==anticipate for actual, anticipate in zip(execut, anticipated_execut) )
            return success
        else:
            # TODO: Log failed prediction attempt to write_key log
            return 0

    def _settle(self, name, value ):
        retrieve_pipe = self.client.pipeline()
        num_delay   = len(self.DELAYS)
        num_windows = len(self._WINDOWS)
        winners_lookup = dict( [ (delay_ndx,dict()) for delay_ndx in range(num_delay) ] )
        for delay_ndx, delay in enumerate(self.DELAYS):
            samples_name = self._samples_name(name=name, delay=delay)
            retrieve_pipe.zcard(samples_name)                                                 # Total number of entries
            retrieve_pipe.smembers( self._sample_owners_name(name=name, delay=delay) )        # List of owners
            for window_ndx, window in enumerate(self._WINDOWS):
                winners_lookup[delay_ndx][window_ndx] = len(retrieve_pipe)                    # Robust to insertion of new instructions in the pipeline
                retrieve_pipe.zrangebyscore( name=samples_name, min=value-window,  max=value+window,  withscores=False)

        # Execute pipeline and re-arrange results
        K = 2 + len(self._WINDOWS)
        assert num_delay*K==len(retrieve_pipe), "Indexing thrown off by change in pipeline"
        retrieved = retrieve_pipe.execute()
        pools            = retrieved[0::K]
        assert all( ( isinstance(p, (int,float)) for p in pools ))
        participant_sets = retrieved[1::K]
        assert all( isinstance(s,set) for s in participant_sets )

        DEBUG = False
        if DEBUG:
            # Check monotonicity as a further check against pipeline result indexing error
            for delay_ndx in range(num_delay):
                num_winners = list()
                for window_ndx in range(num_windows):
                    winners = retrieved[ winners_lookup[delay_ndx][window_ndx] ]
                    num_winners.append(len(winners))
                assert all( a>=0 for a in np.diff( num_winners ) )


        # Select winners in neighbourhood, trying hard for at least one
        if any(pools):
            payments = Counter()
            for delay_ndx, pool, participant_set in zip( range(num_delay), pools, participant_sets ):
                if pool and len(participant_set)>1:
                    # We have a game !
                    game_payments = Counter( dict( (p,-1.0) for p in participant_set ) )

                    # Enlarge window until we have winner ... probably
                    winning_tickets=list()
                    for window_ndx in range(num_windows):
                        if len(winning_tickets)==0:
                            winners_ndx = winners_lookup[delay_ndx][window_ndx]
                            winning_tickets = retrieved[winners_ndx]

                    if len(winning_tickets) == 0:
                        carryover = Counter({self._RESERVE: 1.0 * pool / self.NUM_PREDICTIONS})
                        game_payments.update(carryover)
                    else:
                        winners  = [self._scenario_owner(ticket) for ticket in winning_tickets]
                        reward   = ( 1.0*pool/self.NUM_PREDICTIONS ) / len(winners)   # Could augment this to use kernel or whatever
                        payouts  = Counter( dict( [(w,reward*c) for w,c in Counter(winners).items() ]) )

                        game_payments.update(payouts)
                    if abs(sum( game_payments.values() ))>0.1:
                        # This can occur if owners gets out of sync with the scenario hash ... which it should not
                        # FIXME: Raise system alert and/or garbage cleanup of owner::samples::delay::name versus samples::delay::name
                        raise Exception("Leakage in zero sum game")
                    payments.update(game_payments)

            if len(payments):
                pay_pipe = self.client.pipeline()
                for (recipient, amount) in payments.items():
                    pay_pipe.hincrbyfloat(name=self._BALANCES, key=recipient, amount=float(amount))
                return pay_pipe.execute()
        return 0

    # --------------------------------------------------------------------------
    #            Implementation  (getters)
    # --------------------------------------------------------------------------

    def _get_balance_implementation(self, write_key=None, write_keys=None, aggregate=True):
        write_keys = write_keys or [ write_key ]
        balances   = self.client.hmget(self._BALANCES, *write_keys)
        fixed_balances = [ float( b or "0") for b in balances ]
        return np.nansum( fixed_balances ) if aggregate else fixed_balances

    def _get_lagged_implementation(self, name, with_times, with_values, to_float, start=0, end=None, count=100 ):
        count = count or self.LAGGED_LEN
        end = end or start + count
        get_pipe = self.client.pipeline()
        if with_values:
            get_pipe.lrange(self.lagged_values_name(name), start=start, end=end)
        if with_times:
            get_pipe.lrange(self.lagged_times_name(name=name), start=start, end=end)
        res = get_pipe.execute()
        if with_values and with_times:
            raw_values = res[0]
            raw_times  = res[1]
        elif with_values and not with_times:
            raw_values = res[0]
            raw_times  = None
        elif with_times and not with_values:
            raw_times  = res[0]
            raw_values = None

        if raw_values and to_float:
            try:
                values = RedizConventions.to_float(raw_values)
            except:
                values = raw_values
        else:
            values = raw_values

        if raw_times and to_float:
            times  = RedizConventions.to_float(raw_times)
        else:
            times  = raw_times

        if with_values and with_times:
            return zip(times, values )
        elif with_values and not with_times:
            return values
        elif with_times and not with_values:
            return times

    def _get_delayed_implementation(self, name, delay=None, delays=None, to_float=True):
        """ Get delayed values from one or more names """
        singular = delays is None
        delays = delays or [delay]
        full_names = [self.delayed_name(name=name, delay=delay) for delay in delays]
        delayed = self.client.mget(*full_names)
        if to_float:
            try:
                delayed = RedizConventions.to_float( delayed )
            except:
                pass
        return delayed[0] if singular else delayed

    def _get_implementation(self, name: Optional[str] = None,
                            names: Optional[NameList] = None, **nuissance):
        """ Retrieve value(s). No permission required. """
        plural = names is not None
        names = names or [name]
        res = self._pipelined_get(names=names)
        return res if plural else res[0]

    def _pipelined_get(self, names):
        # Why not mget ??
        if len(names):
            get_pipe = self.client.pipeline(transaction=True)
            for name in names:
                get_pipe.get(name=name)
            return get_pipe.execute()

    def _get_history_implementation(self, name, min, max, count, populate, drop_expired ):
        """ Retrieve history, optionally replacing pointers with actual values  """
        history = self.client.xrevrange(name=self.HISTORY+name, min=min, max=max, count=count )
        if populate:
            has_pointers = any(self._POINTER in record for record in history)
            if has_pointers and populate:
                pointers = dict()
                for k, record in enumerate(history):
                    if self._POINTER in record:
                        pointers[k] = record[self._POINTER]

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


    def _get_links_implementation(self, name, delay=None, delays=None):
        if delay is None and delays is None:
            delays = self.DELAYS
            singular = False
        else:
            singular = delays is None
            delays = delays or [ delay ]
        links = [ self.client.hgetall(self.links_name(name=name, delay=delay)) for delay in delays]
        return links[0] if singular else links

    def _get_backlinks_implementation(self, name):
        return self.client.hgetall(self.backlinks_name(name=name))

    def _get_subscribers_implementation(self, name):
        return list(self.client.smembers(self.subscribers_name(name=name)))

    def _get_subscriptions_implementation(self, name):
        return list(self.client.smembers(self.subscriptions_name(name=name)))

    def _get_predictions_implementation(self, name, delay=None, delays=None, obscure=True):
        return self._get_distribution(namer=self._predictions_name, name=name, delay=delay, delays=delays, obscure=obscure)

    def _get_samples_implementation(self, name, delay=None, delays=None, obscure=True):
        return self._get_distribution( namer=self._samples_name, name=name, delay=delay, delays=delays, obscure=obscure )

    def _get_distribution(self, namer, name, delay=None, delays=None, obscure=True):
        """ Get predictions or samples and obfuscate the write keys """
        singular = delays is None
        delays   = delays or [delay]
        distribution_names  = [ namer(name=name,delay=delay) for delay in delays ]
        pipe = self.client.pipeline()
        for distribution_name in distribution_names:
            pipe.zrange(name=distribution_name, start=0, end=-1, withscores=True )
        private_distributions = pipe.execute()
        data = list()
        for distribution in private_distributions:
            if obscure:
                _data = dict([(self._make_scenario_obscure(scenario), v) for (scenario, v) in distribution])
            else:
                _data = dict([(scenario, v) for (scenario, v) in distribution])
            data.append(_data)
        return data[0] if singular else data
