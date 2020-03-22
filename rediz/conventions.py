import re, sys, json, math, time, os, uuid, muid
import pymorton
from itertools import zip_longest
import numpy as np
from redis.client import list_or_args
from typing import List, Union, Any, Optional
from microprediction.conventions import MicroConventions

KeyList   = List[Optional[str]]
NameList  = List[Optional[str]]
Value     = Union[str,int]
ValueList = List[Optional[Value]]
DelayList = List[Optional[int]]

SEP = "::"

REDIZ_CONVENTIONS_ARGS = ('history_len', 'lagged_len', 'delays', 'max_ttl', 'error_ttl', 'transactions_ttl','error_limit', 'num_predictions','windows','obscurity','delay_grace','instant_recall')
MICRO_CONVENTIONS_ARGS = ('min_len','min_balance')

class RedizConventions(MicroConventions):

    def __init__(self,history_len=None, lagged_len=None, delays=None, max_ttl=None, error_ttl=None, transactions_ttl=None,
                  error_limit=None, num_predictions=None, windows=None,
                  obscurity=None, delay_grace=None, instant_recall=None, min_len=None, min_balance=None ):

        super().__init__(min_len=min_len,min_balance=min_balance,num_predictions=num_predictions)

        if windows is None:
            windows = [1e-4, 1e-3,  1e-2]
        self.SEP = SEP
        self.COPY_SEP = self.SEP + "copy" + self.SEP
        self.PREDICTION_SEP = self.SEP + "prediction" + self.SEP

        # User facing conventions: transparent use of prefixing
        self.DELAYED = "delayed" + self.SEP
        self.CDF = 'cdf'+self.SEP
        self.LINKS = "links" + self.SEP
        self.BACKLINKS = "backlinks" + self.SEP
        self.MESSAGES = "messages" + self.SEP
        self.HISTORY = "history" + self.SEP
        self.HISTORY_LEN = int( history_len or 1000)
        self.LAGGED = "lagged"+self.SEP
        self.LAGGED_VALUES = "lagged_values" + self.SEP
        self.LAGGED_TIMES = "lagged_times" + self.SEP
        self.LAGGED_LEN = int( lagged_len or 10000)
        self.SUBSCRIBERS = "subscribers" + self.SEP
        self.SUBSCRIPTIONS = "subscriptions" + self.SEP
        self.TRANSACTIONS = "transactions" + self.SEP
        self.PREDICTIONS = "predictions"+ self.SEP
        self.SAMPLES = "samples" + self.SEP
        self.BALANCE = "balance" + self.SEP
        self.PERFORMANCE = "performance" + self.SEP
        self.LEADERBOARD = "leaderboard" + self.SEP
        self.SUMMARY = "summary" + self.SEP

        # Logging
        self.CONFIRMS = "confirms" + self.SEP
        self.WARNINGS = "warnings" + self.SEP
        self.ERRORS   = "errors" + self.SEP
        self.WARNINGS_TTL = int(60 * 60)  # TODO: allow configuation
        self.WARNINGS_LIMIT = 1000
        self.CONFIRMS_TTL = int(error_ttl or 60 * 60)  # Number of seconds that set execution error logs are persisted
        self.ERROR_TTL = int(error_ttl or 60 * 60)  # Number of seconds that set execution error logs are persisted
        self.CONFIRMS_TTL = int(error_ttl or 60 * 60)  # Number of seconds that set execution error logs are persisted
        self.ERROR_LIMIT = int(error_limit or 1000)  # Number of error messages to keep per write key
        self.CONFIRMS_LIMIT = int(error_limit or 1000)  # Number of error messages to keep per write key

        # User transparent temporal and other config
        self.MIN_LEN = int(self.min_len)                     # FIXME: Get rid of MIN_LEN
        self.MIN_BALANCE = int(self.min_balance)             # FIXME: Get rid of MIN_BALANCE
        self.NUM_PREDICTIONS = int(self.num_predictions)     # Number of scenerios in a prediction batch
        self.DELAYS = delays or [1, 5]
        self.CONFIRMS_MAX = 5  # Maximum number of confirmations when using mset()
        self.NOISE = 0.3 / self.NUM_PREDICTIONS  # Tie-breaking / smoothing noise added to predictions

        # Implementation details: private reserved redis keys and prefixes.
        self._obscurity = (obscurity or "obscure") + self.SEP
        self._RESERVE = self._obscurity + "reserve"  # Reserve of credits fed by rare cases when all models miss wildly
        self._OWNERSHIP = self._obscurity + "ownership"  # Official map from name to write_key
        self._BLACKLIST = self._obscurity + "blacklist"  # List of discarded keys
        self._NAMES = self._obscurity + "names"  # Redundant set of all names (needed for random sampling when collecting garbage)
        self._PROMISES = self._obscurity + "promises" + self.SEP  # Prefixes queues of operations that are indexed by epoch second
        self._POINTER = self._obscurity + "pointer"  # A convention used in history stream
        self._BALANCES = self._obscurity + "balances"  # Hash of all balances attributed to write_keys
        self._PREDICTIONS = self._obscurity + self.PREDICTIONS  # Prefix to a listing of contemporaneous predictions by horizon. Must be private as this contains write_keys
        self._OWNERS = "owners" + self.SEP  # Prefix to a redundant listing of contemporaneous prediction owners by horizon. Must be private as this contains write_keys
        self._SAMPLES = self._obscurity + self.SAMPLES  # Prefix to delayed predictions by horizon. Contain write_keys !
        self._PROMISED = "promised" + self.SEP  # Prefixes temporary values referenced by the promise queue

        # Other implementation config
        self._DELAY_GRACE = int(delay_grace or 5)  # Seconds beyond the schedule time when promise data expires
        self._DEFAULT_MODEL_STD = 1.0  # Noise added for self-prediction
        self._WINDOWS = windows  # Sizes of neighbourhoods around truth used in countback ... don't make too big or it hits performance
        self._INSTANT_RECALL = instant_recall or False
        self._MAX_TTL = int( max_ttl or 60 * 60 ) # Maximum TTL, useful for testing
        self._TRANSACTIONS_TTL = int( transactions_ttl or 24 * (60 * 60) )  # How long to keep transactions stream for inactive write_keys


    @staticmethod
    def assert_not_in_reserved_namespace(names, *args):
        names = list_or_args(names, args)
        if any(RedizConventions.sep() in name for name in names):
            raise Exception("Operation attempted with a name that uses " + RedizConventions.sep())


    @staticmethod
    def is_vector_value(value):
        if isinstance(value, (list, tuple)):
            return all((RedizConventions.is_scalar_value(v) for v in value))
        else:
            try:
                v = json.loads(value)
                return RedizConventions.is_vector_value(v)
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
        return np.array(values, dtype=float).tolist()

    @staticmethod
    def coerce_inputs(  names:Optional[NameList]=None,
                         values:Optional[ValueList]=None,
                         write_keys:Optional[KeyList]=None,
                         name:Optional[str]=None,
                         value:Optional[Any]=None,
                         write_key:Optional[str]=None,
                         budget:Optional[int]=None,
                         budgets:Optional[List[int]]=None):
        # Convention for broadcasting optional singleton inputs to arrays
        names   = names or [ name ]
        values  = values or [ value for _ in names ]
        budgets = budgets or [ budget for _ in names ]
        write_keys = write_keys or [ write_key for _ in names ]
        return names, values, write_keys, budgets

    @staticmethod
    def delay_as_int(delay):
        """ By convention, None means no delay """
        return 0 if delay is None else int(delay)

    def percentile_name(self, name, delay):
        return self.zcurve_name(names=[name],delay=delay)

    def identity(self, name):
        return name

    def delayed_name(self, name, delay):
        return self.DELAYED + str(delay) + self.SEP + name

    def messages_name(self, name):
        return self.MESSAGES + name

    def confirms_name(self, write_key):
        return self.CONFIRMS + write_key + '.json'

    def errors_name(self, write_key):
        return self.MESSAGES + write_key + '.json'

    def warnings_name(self, write_key):
        return self.WARNINGS + write_key + '.json'

    def transactions_name(self, write_key=None, name=None, delay=None ):
        """ Stream name """
        delay     = None if delay is None else str(delay)
        key_stem  = None if write_key is None else os.path.splitext(write_key)[0]
        name_stem = None if name is None else os.path.splitext(name)[0]
        tail = self.SEP.join( [ s for s in [key_stem,delay,name_stem] if s is not None ])
        return self.TRANSACTIONS + tail + '.json'

    def performance_name(self, write_key):
        return self.PERFORMANCE + write_key + '.json'

    def performance_key(self, name, delay):
        name_stem = os.path.splitext(name)[0]
        return name_stem + self.SEP + str(delay)

    def leaderboard_name(self, name=None, delay=None):
        if name is None and delay is None:
            return self.LEADERBOARD[:-2]+'.json'
        else:
            return self.LEADERBOARD+name if delay is None else self.LEADERBOARD+str(delay)+self.SEP+name

    def history_name(self, name):
        return self.HISTORY + name

    def lagged_values_name(self, name):
        return self.LAGGED_VALUES + name

    def lagged_times_name(self, name):
        return self.LAGGED_TIMES + name

    def links_name(self, name, delay):
        return self.LINKS + str(delay) + self.SEP + name

    def backlinks_name(self, name):
        return self.BACKLINKS + name

    def subscribers_name(self, name):
        return self.SUBSCRIBERS + name

    def subscriptions_name(self, name):
        return self.SUBSCRIPTIONS + name


    @staticmethod
    def chunker(results, n):
        """ Assumes there are n*k operations and just chunks the results into groups of length k """

        def grouper(iterable, n, fillvalue=None):
            args = [iter(iterable)] * n
            return zip_longest(*args, fillvalue=fillvalue)

        m = int(len(results) / n)
        return list(grouper(iterable=results, n=m, fillvalue=None))

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

    def _nullary_methods(self):
        return {"name": self.identity,
                "lagged": self.lagged_values_name,
                "lagged_times": self.lagged_times_name,
                "backlinks": self.backlinks_name,
                "subscribers": self.subscribers_name,
                "subscriptions": self.subscriptions_name,
                "history": self.history_name,
                "messages": self.messages_name}

    def _delay_methods(self):
        return {"delayed": self.delayed_name,
                "links": self.links_name}

    def cdf_name(self,name,delay=None):
        return self.CDF + name if delay==None else self.CDF+str(delay)+self.SEP+name





    # --------------------------------------------------------------------------
    #           Private conventions (names, places, formats, ttls )
    # --------------------------------------------------------------------------

    def _private_delay_methods(self):
        return {"participants": self._sample_owners_name,
                "predictions": self._predictions_name,
                "samples": self._samples_name
                }

    def _private_derived_names(self, name):
        references = dict()
        for method_name, method in self._private_delay_methods().items():
            for delay in self.DELAYS:
                item = {method_name + self.SEP + str(delay): method(name=name, delay=delay)}
                references.update(item)
        return references

    def _names(self):
        return list(self.client.smembers(self._NAMES))

    def _ownership_name(self):
        return self._OWNERSHIP

    def _random_promised_name(self, name):
        name_stem = os.path.splitext(name)[0]
        return self._PROMISED + str(uuid.uuid4())[:8] + self.SEP + name_stem + '.json'

    def _copy_promise(self, source, destination):
        return source + self.COPY_SEP + destination

    def _promise_queue_name(self, epoch_seconds):
        return self._PROMISES + str(int(epoch_seconds))

    def _sample_owners_name(self, name, delay):
        return self._OWNERS + self._samples_name(name=name,delay=delay)

    def _predictions_name(self, name, delay):
        return self._PREDICTIONS + str(delay) + self.SEP + name

    def _samples_name(self, name, delay):
        return self._SAMPLES + str(delay) + self.SEP + name

    def _format_scenario(self, write_key, k):
        """ A "ticket" indexed by write_key and an index from 0 to self.NUM_PREDiCTIONS-1 """
        return str(k).zfill(8) + self.SEP + write_key

    def _make_scenario_obscure(self, ticket):
        """ Change write_key to a hash of write_key """
        parts = ticket.split(self.SEP)
        return parts[0] + self.SEP + muid.shash(parts[1])

    def _scenario_percentile(self, scenario):
        """ Extract scenario percentile from scenario string """
        return (0.5 + float(scenario.split(self.SEP)[0])) / self.NUM_PREDICTIONS

    def _scenario_owner(self, scenario):
        """ Extract owner of a scenario from scenario string """
        return scenario.split(self.SEP)[1]

    def _prediction_promise(self, target, delay, predictions_name):
        """ Format for a promise that sits in a promise queue waiting to be inserted into samples::1::name, for instance """
        return predictions_name + self.PREDICTION_SEP + self._samples_name(name=target, delay=delay)

    def _interpret_delay(self, delay_name):
        """ Extract root name and delay in seconds as int from  delayed::600:name """
        assert self.DELAYED in delay_name
        parts = delay_name.split(self.SEP)
        root = parts[-1]
        delay = int(parts[-2])
        return root, delay


    # --------------------------------------------------------------------------
    #           Private getters
    # --------------------------------------------------------------------------

    def _get_sample_owners(self, name, delay):
        """ Set of participants in a market """
        return list(self.client.smembers(self._sample_owners_name(name=name, delay=delay)))

    def _pools(self, names, delays):
        """ Return count of number of scenarios in predictions::5::name, predictions::1::name  for name in names
               Returns:  pools    { name: [ 5000, 1000, 0, 0 ] }
        """
        pools = dict([(n, list()) for n in names])
        pool_pipe = self.client.pipeline()
        ndxs = dict([(n, list()) for n in names])
        for name in names:
            for delay in delays:
                ndxs[name].append(len(pool_pipe))
                pool_pipe.zcard(self._predictions_name(name=name, delay=delay))
        exec = pool_pipe.execute()
        for name in names:
            for delay_ndx in range(len(delays)):
                pools[name].append(exec[ndxs[name][delay_ndx]])
        return pools


    # --------------------------------------------------------------------------
    #            Economic model for data storage
    # --------------------------------------------------------------------------

    def _promise_ttl(self):
        return max(self.DELAYS) + self._DELAY_GRACE

    def _cost_based_history_len(self, value):
        return self.HISTORY_LEN    # TODO: Could be refined

    def _cost_based_lagged_len(self, value ):
        t = time.time()
        sz = (sys.getsizeof(value) + sys.getsizeof(t)) + 10
        return int( math.ceil( 10 * self.LAGGED_LEN / sz) )

    def _cost_based_ttl(self, value, budget):
        """ Time to live for name implies a minimal update frequency """
        return RedizConventions._value_ttl(value=value, budget=budget, num_delays=len(self.DELAYS), max_ttl=self._MAX_TTL )

    def _cost_based_distribution_ttl(self,budget):
        """ Time to live for samples ... mostly budget independent """
        return int( max(self.DELAYS)+self._DELAY_GRACE+60+budget )

    # --------------------------------------------------------------------------
    #            Redis version/capability inference
    # --------------------------------------------------------------------------

    def _streams_support(self):
        # Returns True if redis streams are supported by the redis client
        # (Note that streams are not supported on fakeredis)
        try:
            record_of_test = {"time": str(time.time())}
            self.client.xadd(name='e5312d16-dc87-46d7-a2e5-f6a6225e63a5', fields=record_of_test)
            return True
        except:
            return False


    # --------------------------------------------------------------------------
    #           Statistics
    # --------------------------------------------------------------------------

    def normcdf(self, x):
        g = self._normcdf_function()
        return g(x)

    def norminv(self,p):
        f = self._norminv_function()
        return f(p)

    @staticmethod
    def to_zscores(prctls):
        norminv = RedizConventions._norminv_function()
        return [ norminv(p) for p in prctls ]


    @staticmethod
    def _norminv_function():
        try:
            from statistics import NormalDist
            return NormalDist(mu=0, sigma=1.0).inv_cdf
        except ImportError:
            from scipy.stats import norm
            return norm.ppf

    @staticmethod
    def _normcdf_function():
        try:
            from statistics import NormalDist
            return NormalDist(mu=0, sigma=1.0).cdf
        except ImportError:
            from scipy.stats import norm
            return norm.cdf

    @staticmethod
    def _zmean_percentile(ps):
        """ Given a vector of percentiles, returns normal percentile of the mean zscore """
        if len(ps):
            norminv = RedizConventions._norminv_function()
            zscores = [norminv(p) for p in ps]
            avg_zscore = np.nanmean(zscores)
            normcdf = RedizConventions._normcdf_function()
            avg_p = normcdf(avg_zscore)
            return avg_p
        else:
            return 0.5

    # --------------------------------------------------------------------------
    #           Z-order curves
    # --------------------------------------------------------------------------

    def zcurve_names(self, names):
        import itertools
        znames=list()
        for delay in self.DELAYS:
           for dim in [1,2,3]:
                name_combinations = itertools.combinations(sorted(names),dim)
                zname = self.zcurve_name( names=name_combinations,delay=delay )
                znames.append(zname)
        return znames

    def zcurve_name(self, names, delay, obscure=False):
        """ Naming convention for derived quantities, called zcurves """
        basenames = sorted( [n.split('.')[-2] for n in names] )
        prefix    = "z" + str(len(names))
        clearbase = "~".join( [prefix] + basenames + [str(delay)] )
        return clearbase+'.json' if not obscure else RedizConventions.hash(clearbase)+'.json'

    @staticmethod
    def morton_scale(dim):
        return 2**10

    @staticmethod
    def morton_large(dim):
        SCALE = RedizConventions.morton_scale(dim=dim)
        return pymorton.interleave( *[ SCALE-1 for _ in range(dim) ] )

    def to_zcurve(self, prctls: List[float] ):
        """ A mapping from R^n -> R based on the Morton z-curve """
        dim = len(prctls)
        if dim==1:
            return self.to_zscores(prctls)[0]
        else:
            SCALE = RedizConventions.morton_scale(dim)
            int_prctls = [ int(math.floor(p*SCALE)) for p in prctls ]
            m1         = pymorton.interleave(*int_prctls)
            int_prctls_back = pymorton.deinterleave2(m1) if dim==2 else  pymorton.deinterleave3(m1)
            assert all( i1==i2 for i1,i2 in zip(int_prctls, int_prctls_back))
            m2         = pymorton.interleave(*[ SCALE-1 for _ in range(dim) ])
            zpercentile =  m1/m2
            return self.norminv(zpercentile)

    def from_zcurve(self, zvalue, dim):
        zpercentile = self.normcdf(zvalue)
        SCALE = self.morton_scale(dim)
        zmorton     = int( self.morton_large(dim)*zpercentile+0.5 )
        if dim==2:
            values  = pymorton.deinterleave2(zmorton)
        elif dim==3:
            values  = pymorton.deinterleave3(zmorton)
        prtcls = [ v/SCALE for v in values ]
        return prtcls



    # --------------------------------------------------------------------------
    #           Default scenario generation
    # --------------------------------------------------------------------------

    def empirical_predictions(self, lagged_values ):
        from rediz.samplers import exponential_bootstrap
        predictions = exponential_bootstrap(lagged=lagged_values, decay=0.005, num=self.NUM_PREDICTIONS)
        return sorted(predictions)

    # --------------------------------------------------------------------------
    #           Time to live economics
    # --------------------------------------------------------------------------

    @staticmethod
    def _value_ttl(value, budget, num_delays, max_ttl ):
        # Assign a time to live that won't break the bank
        REPLICATION = 1 + 2 * num_delays
        BLOAT = 3
        DOLLAR = 10000.  # Credits per dollar
        COST_PER_MONTH_10MB = 1. * DOLLAR
        COST_PER_MONTH_1b = COST_PER_MONTH_10MB / (10 * 1000 * 1000)
        SECONDS_PER_DAY = 60. * 60. * 24.
        SECONDS_PER_MONTH = SECONDS_PER_DAY * 30.
        FIXED_COST_bytes = 10  # Overhead
        num_bytes = sys.getsizeof(value)
        credits_per_month = REPLICATION * BLOAT * (num_bytes + FIXED_COST_bytes) * COST_PER_MONTH_1b
        ttl_seconds = int(math.ceil(SECONDS_PER_MONTH / credits_per_month))
        ttl_seconds = budget * ttl_seconds
        ttl_seconds = min(ttl_seconds, max_ttl)
        return int( ttl_seconds )
