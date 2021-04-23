import fakeredis, sys, math, json, redis, time, random, itertools, datetime
import numpy as np
from collections import Counter, OrderedDict
from typing import List, Union, Any, Optional
from redis.client import list_or_args
from redis.exceptions import DataError
from .conventions import RedizConventions, REDIZ_CONVENTIONS_ARGS, MICRO_CONVENTIONS_ARGS, KeyList, NameList, ValueList
from rediz.utilities import get_json_safe, has_nan, shorten, stem
from pprint import pprint

# REDIZ
# -----
# Implements a write-permissioned shared REDIS value store with subscription, history, prediction, clearing
# and delay mechanisms. Intended for collectivized short term (e.g. 1 minute or 15 minutes) prediction.

PY_REDIS_ARGS = (
    'host', 'port', 'db', 'username', 'password', 'socket_timeout', 'socket_keepalive', 'socket_keepalive_options',
    'connection_pool', 'unix_socket_path', 'encoding', 'encoding_errors', 'charset', 'errors',
    'decode_responses', 'retry_on_timeout', 'ssl', 'ssl_keyfile', 'ssl_certfile', 'ssl_cert_reqs', 'ssl_ca_certs',
    'ssl_check_hostname', 'max_connections', 'single_connection_client', 'health_check_interval', 'client_name')
FAKE_REDIS_ARGS = ('decode_responses',)


class Rediz(RedizConventions):

    # Initialization

    def __init__(self, **kwargs):
        # Set some system parameters
        conventions_kwargs = dict(
            [(k, v) for k, v in kwargs.items() if k in REDIZ_CONVENTIONS_ARGS or k in MICRO_CONVENTIONS_ARGS])
        for arg in MICRO_CONVENTIONS_ARGS:
            if not arg in conventions_kwargs:
                raise Exception('Must supply ' + arg)

        super().__init__(**conventions_kwargs)
        # Initialize Rediz instance. Expects host, password, port   ... or default to fakeredis
        for k in conventions_kwargs.keys():
            kwargs.pop(k)
        self.client = self.make_redis_client(**kwargs)

    # --------------------------------------------------------------------------
    #            Public interface - getters
    # --------------------------------------------------------------------------

    def card(self):
        return self.client.scard(self._NAMES)

    def exists(self, name):
        return self.client.sismember(name=self._NAMES, value=name)

    def size(self, name):
        return self._size_implementation(name=name, with_report=False, with_private=True)

    def _size(self, name, with_report=False):
        return self._size_implementation(name=name, with_report=with_report, with_private=True)

    def get_donation_password(self):
        return self.shash(self._obscurity)

    def get_donors(self):
        donors = self.client.hgetall(self.donors_name())
        return dict(sorted(donors.items(), key=lambda e: int(e[1]), reverse=True))

    def get_donations(self, len=None, with_key=False):
        if len is None:
            len = 12
        if with_key:
            return [(write_key, self.animal_from_key(write_key)) for write_key in
                    self.client.smembers(self.donation_name(len=len))]
        else:
            return [self.animal_from_key(write_key) for write_key in self.client.smembers(self.donation_name(len=len))]

    def get(self, name, as_json=False, **kwargs):
        """ Unified getter expecting prefixed name - used by web application """
        parts = name.split(self.SEP)
        kwargs.update({"as_json": as_json})
        if len(parts) == 1:
            data = self._get_implementation(name=name, **kwargs)
        else:
            data = self._get_prefixed_implementation(prefixed_name=name)

        if isinstance(data, set):
            data = list(set)
        return json.dumps(data) if as_json else data

    def mget(self, names: NameList, *args):
        names = list_or_args(names, args)
        return self._get_implementation(names=names)

    def get_samples(self, name, delay=None, delays=None):
        return self._get_samples_implementation(name=name, delay=delay, delays=delays)

    def get_index(self):
        return self._get_index_implementation()

    def get_predictions(self, name, delay=None, delays=None):
        return self._get_predictions_implementation(name=name, delay=delay, delays=delays)

    def get_cdf(self, name:str, delay, values:[float]=None, top=10, min_balance=-50000000):
        """ Retrieve 'x' and 'y' values representing an approximate CDF
        :param values:   Abscissa for CDF ... if not supplied it will try to figure out something
        :param top:      Number of top participants to use
        :return:  {'x':[float],'y':[float]}
        """
        delay = int(delay)
        # TODO: Change to min_rating instead of min_balance
        if values is None:
            lagged_values = self.get_lagged_values(name=name)
            values = self.cdf_values(lagged_values=lagged_values,num=20,as_discrete=None)
        return self._get_cdf_implementation(name=name, delay=delay, values=values, top=top, min_balance=min_balance)

    def get_reserve(self):
        return float(self.client.hget(self._BALANCES, self._RESERVE) or 0)

    def get_delayed(self, name, delay=None, delays=None, to_float=True):
        return self._get_delayed_implementation(name=name, delay=delay, delays=delays, to_float=to_float)

    def get_lagged(self, name, start=0, end=None, count=1000, to_float=True):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=True,
                                               with_times=True, to_float=to_float)

    def get_lagged_values(self, name, start=0, end=None, count=1000, to_float=True):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=True,
                                               with_times=False, to_float=to_float)

    def get_lagged_times(self, name, start=0, end=None, count=1000, to_float=True):
        return self._get_lagged_implementation(name, start=start, end=end, count=count, with_values=False,
                                               with_times=True, to_float=to_float)

    def get_history(self, name, max='+', min='-', count=100, populate=True, drop_expired=True):
        return self._get_history_implementation(name=name, max=max, min=min, count=count, populate=populate,
                                                drop_expired=drop_expired)

    def get_subscriptions(self, name):
        return self._get_subscriptions_implementation(name=name)

    def get_subscribers(self, name):
        return self._get_subscribers_implementation(name=name)

    def get_errors(self, write_key, start=0, end=-1):
        return self.client.lrange(name=self.errors_name(write_key=write_key), start=start, end=end)

    def get_warnings(self, write_key, start=0, end=-1):
        return self.client.lrange(name=self.warnings_name(write_key=write_key), start=start, end=end)

    def delete_errors(self, write_key):
        return self.client.delete(self.errors_name(write_key=write_key))

    def delete_warnings(self, write_key):
        return self.client.delete(self.warnings_name(write_key=write_key))

    def get_confirms(self, write_key, start=0, end=-1):
        return self.client.lrange(name=self.confirms_name(write_key=write_key), start=start, end=end)

    def delete_confirms(self, write_key):
        return self.client.delete(self.confirms_name(write_key=write_key))

    def get_balance(self, write_key):
        return float(self.client.hget(name=self._BALANCES, key=write_key) or 0)

    def transfer(self, source_write_key, recipient_write_key, amount=None, as_record=False):
        return self._transfer_implementation(source_write_key=source_write_key, recipient_write_key=recipient_write_key,
                                             amount=amount, as_record=as_record)

    @staticmethod
    def _nice_and_ordered(d):
        """ Present redis hashes as dict in decending order of value """
        d_tuples = list([(ky, float(val)) for ky, val in d.items()])
        d_tuples.sort(key=lambda t: t[1], reverse=True)
        return OrderedDict(d_tuples)

    def get_budget(self, name):
        return self.client.hget(name=self.BUDGETS, key=name)

    def get_repository(self, write_key):
        """ Accepts write_key or code """
        return self.client.hget(name=self._REPOS, key=self.shash(write_key)) if self.is_valid_key(
            write_key) else self.client.hget(name=self._REPOS, key=write_key)

    def set_repository(self, write_key, url):
        if self.is_valid_key(write_key):
            code = self.shash(write_key)
            return self.client.hset(name=self._REPOS, key=code, value=url)
        else:
            self._error(write_key=write_key, data={'operation': 'set_repo', 'write_key': write_key, 'url': url,
                                                   'message': 'write key not valid'})
            return 0

    def delete_repository(self, write_key):
        if self.is_valid_key(write_key):
            code = self.shash(write_key)
            return self.client.hdel(self._REPOS, code)
        else:
            self._error(write_key=write_key,
                        data={'operation': 'delete_repo', 'write_key': write_key, 'message': 'write key not valid'})
            return 0

    def get_awards(self, write_key):
        """ Accepts write_key or code """
        val = self.client.hget(name=self._AWARDS, key=self.shash(write_key)) if self.is_valid_key(
            write_key) else self.client.hget(name=self._AWARDS, key=write_key)
        return json.loads(val)

    def get_budgets(self):
        return self._nice_and_ordered(self.client.hgetall(name=self.BUDGETS))

    def get_volumes(self):
        return self._nice_and_ordered(self.client.hgetall(name=self.VOLUMES))

    def get_sponsors(self):
        ownership = self.client.hgetall(self._OWNERSHIP)
        obscured = [(name, self.animal_from_key(key)) for name, key in ownership.items()]
        obscured.sort(key=lambda t: len(t[1]))
        return OrderedDict(obscured)

    def get_links(self, name, delay=None, delays=None):
        assert not self.SEP in name, "Intent is to provide delay variable"
        return self._get_links_implementation(name=name, delay=delay, delays=delays)

    def get_backlinks(self, name):
        return self._get_backlinks_implementation(name=name)

    def get_transactions(self, max='+', min='-', count=50, write_key=None, name=None, delay=None):
        return self._get_transactions_implementation(max=max, min=min, count=count, write_key=write_key, name=name,
                                                     delay=delay)

    def get_summary(self, name):
        assert self._root_name(name) == name
        return self._get_summary_implementation(name)

    def get_home(self, write_key):
        return self._get_home_implementation(write_key=write_key)

    # ---------------------------
    #        Leaderboards
    # ---------------------------

    def get_leaderboard(self, name=None, delay=None, count=1200, with_repos=False):
        return self._get_leaderboard_implementation(name=name, delay=delay, count=count, with_repos=with_repos)

    def get_previous_monthly_overall_leaderboard(self, with_repos=False):
        last_month_day = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=2)
        return self._get_custom_leaderboard_implementation(sponsor_code=None, dt=last_month_day, count=200,
                                                           with_repos=with_repos)

    def get_monthly_overall_leaderboard(self, with_repos=False):
        return self._get_custom_leaderboard_implementation(sponsor_code=None, dt=datetime.datetime.now(), count=200,
                                                           with_repos=with_repos)

    # By sponsor ...
    # Allow user to pass either a write_key or a write_code (recall code = shash(key) )

    def code_from_code_or_key(self, sponsor):
        if self.is_valid_key(sponsor):
            return self.shash(sponsor)
        elif self.animal_from_code(sponsor):
            return sponsor

    def delete_regular_monthly_sponsored_leaderboard(self, write_key):
        sponsor = self.shash(write_key)
        self._delete_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='regular.json')

    def multiply_regular_monthly_sponsored_leaderboard(self, write_key, weight=0.97):
        sponsor = self.shash(write_key)
        self._multiply_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='regular.json', weight=weight)

    def delete_overall_monthly_sponsored_leaderboard(self, write_key):
        sponsor = self.shash(write_key)
        self._delete_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name=None)

    def multiply_bivariate_monthly_sponsored_leaderboard(self, write_key, weight=0.9):
        sponsor = self.shash(write_key)
        self._multiply_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='z2~blah.json', weight=weight)

    def delete_bivariate_monthly_sponsored_leaderboard(self, write_key):
        sponsor = self.shash(write_key)
        self._delete_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='z2~blah.json')

    def multiply_trivariate_monthly_sponsored_leaderboard(self, write_key, weight=0.9):
        sponsor = self.shash(write_key)
        self._multiply_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='z3~blah.json',weight=weight)

    def delete_trivariate_monthly_sponsored_leaderboard(self, write_key):
        sponsor = self.shash(write_key)
        self._delete_custom_leaderboard_implementation(sponsor_code=sponsor, dt=None, name='z3~blah.json')

    def get_regular_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        """ Excludes z's """
        code = self.code_from_code_or_key(sponsor)
        if code:
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=None, count=200, name='mystream',
                                                               with_repos=with_repos)

    def get_zscore_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        code = self.code_from_code_or_key(sponsor)
        if code:
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=None, count=200, name='z1~',
                                                               with_repos=with_repos)

    def get_bivariate_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        code = self.code_from_code_or_key(sponsor)
        if code:
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=None, count=200, name='z2~',
                                                               with_repos=with_repos)

    def get_trivariate_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        code = self.code_from_code_or_key(sponsor)
        if code:
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=None, count=200, name='z3~',
                                                               with_repos=with_repos)

    def get_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        code = self.code_from_code_or_key(sponsor)
        if code:
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=datetime.datetime.now(), count=200,
                                                               with_repos=with_repos)

    def get_previous_monthly_sponsored_leaderboard(self, sponsor, with_repos=False):
        code = self.code_from_code_or_key(sponsor)
        if code:
            last_month_day = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=2)
            return self._get_custom_leaderboard_implementation(sponsor_code=code, dt=last_month_day, count=200,
                                                               with_repos=with_repos)

    def get_messages(self, name, write_key):
        if self._authorize(name=name, write_key=write_key):
            return self._get_messages_implementation(name=name, write_key=write_key)

    # --------------------------------------------------------------------------
    #            Public interface  (set/delete streams)
    # --------------------------------------------------------------------------

    def mtouch(self, names, write_key, budgets=None):
        budgets = budgets or [1 for _ in names]
        return self._mtouch_implementation(names=names, write_key=write_key, budgets=budgets)

    def touch(self, name, write_key, budget=1):
        return self._touch_implementation(name=name, write_key=write_key, budget=budget)

    @staticmethod
    def muid_difficulty(write_key):
        try:
            return Rediz.key_difficulty(write_key)
        except:
            return 0

    def set(self, name, value, write_key, budget=10):
        """ Set name=value and initiate clearing, derived zscore market etc """
        assert RedizConventions.is_plain_name(name), "Expecting plain name"
        assert RedizConventions.is_valid_key(write_key), "Invalid write_key"
        if self.muid_difficulty(write_key) < self.min_len:
            reason = "Write key isn't sufficiently rare to create or update a stream. Must be difficulty " + str(
                self.min_len)
            self._error(write_key=write_key, operation='set', success=False, reason=reason)
            return False
        else:
            return self._mset_implementation(name=name, value=value, write_key=write_key, return_args=None,
                                             budget=budget, with_percentiles=True)

    def cset(self, names: NameList, values: ValueList, budgets: List[int], write_key):
        if self.muid_difficulty(write_key) < self.min_len + 1:
            reason = "Write key isn't sufficiently rare to request joint distributions. Must be difficulty " + str(
                self.min_len + 1)
            self._error(write_key=write_key, operation='set', success=False, reason=reason)
            return False
        else:
            return self.mset(names=names, values=values, budgets=budgets, write_key=write_key, with_copulas=True)

    def mset(self, names: NameList, values: ValueList, budgets: List[int], write_key=None, write_keys=None,
             with_copulas=False):
        """ Apply set() for multiple names and values, with copula derived streams optionally """  # Todo: disallow calling with multiple write_keys
        is_plain = [RedizConventions.is_plain_name(name) for name in names]
        if not len(names) == len(values):
            error_data = {'names': names, 'values': values, 'error': 'Names and values have different lengths'}
            self._error(write_key=write_key, data=error_data)
            raise Exception(json.dumps(error_data))
        if not all(is_plain):
            culprits = [n for n, isp in zip(names, is_plain) if not (isp)]
            error_data = {'culprits': culprits,
                          'error': 'One or more names are not considered plain names. See MicroConvention.is_plain_name '}
            self._error(write_key=write_key, data=error_data)
            raise Exception(json.dumps(error_data))
        else:
            write_keys = write_keys or [write_key for _ in names]
            return self._mset_implementation(names=names, values=values, write_keys=write_keys, return_args=None,
                                             budgets=budgets, with_percentiles=True, with_copulas=with_copulas)

    def delete(self, name, write_key):
        """ Delete/expire all artifacts associated with name (links, subs, markets etc) """
        return self._permissioned_mdelete(name=name, write_key=write_key)

    def mdelete(self, names, write_key: Optional[str] = None, write_keys: Optional[KeyList] = None):
        """ Delete/expire all artifacts associated with multiple names """
        return self._permissioned_mdelete(names=names, write_key=write_key, write_keys=write_keys)

    # --------------------------------------------------------------------------
    #            Public interface  (set/delete scenarios)
    # --------------------------------------------------------------------------

    def set_scenarios(self, name, values, delay, write_key, verbose=False):
        """ Supply scenarios for scalar value taken by name
               values :   [ float ]  len  self.num_predictions
        """
        assert len(values) == self.num_predictions
        assert int(delay) in self.DELAYS, "Invalid choice of delay"
        assert self.is_valid_key(write_key), "Invalid write_key"
        if self.bankrupt(write_key=write_key):
            leaderboard = self._get_leaderboard_implementation(name=name, delay=delay, readable=False, count=10000)
            code = self.shash(key=write_key)
            if (code not in leaderboard) or (leaderboard[code] < -1.0):
                self._error(write_key=write_key,
                            data={'operation': 'submit', 'success': False, 'reason': 'bankruptcy', 'name': name})
                return False

        fvalues = list(map(float, values))
        return self._set_scenarios_implementation(name=name, values=fvalues, delay=delay, write_key=write_key)

    def delete_all_scenarios(self, write_key):
        active = self.get_active(write_key=write_key)
        limit = 5
        for horizon in active:
            name, delay = self.split_horizon_name(horizon)
            self._delete_scenarios_implementation(name=name, write_key=write_key, delay=delay)
            limit = limit - 1
        return limit > 0

    def delete_scenarios(self, name, write_key, delay=None, delays=None):
        """ This will be deprecated in favor of cancel ... """
        return self._delete_scenarios_implementation(name=name, write_key=write_key, delay=delay, delays=delays)

    def cancel(self, name, write_key, delay=None, delays=None):
        return self._cancel_implementation(name=name, write_key=write_key, delay=delay, delays=delays)

    # --------------------------------------------------------------------------
    #            Public interface  (performance)
    # --------------------------------------------------------------------------

    def get_performance(self, write_key):
        performance = self.client.hgetall(name=self.performance_name(write_key=write_key))
        return self._nice_and_ordered(performance)

    def delete_performance(self, write_key):
        return self.client.delete(self.performance_name(write_key=write_key))

    def delete_leaderboard(self, write_key, name, delay=None):
        if self._authorize(name=name, write_key=write_key):
            self._delete_leaderboard_implementation(name=name, delay=delay)

    def _delete_leaderboard_implementation(self, name, delay):
        self.client.delete(self.leaderboard_name(name=name, delay=delay))

    # --------------------------------------------------------------------------
    #            Donations of MUIDs
    # --------------------------------------------------------------------------

    def donate(self, write_key, password, donor=None, verbose=True):
        official_password = self.get_donation_password()
        donor = donor or 'anonymous'
        if password == official_password:
            len = self.key_difficulty(write_key)
            if len >= self.MIN_LEN:
                if self.client.sadd(self.donation_name(len=len), write_key):
                    importance = 16 ** (len - self.MIN_LEN)
                    self.client.hincrby(name=self.donors_name(), key=donor.lower(), amount=importance)
                return {"operation": "donation", "success": True, "message": "Thanks, you can view it at",
                        "url": self.base_url + "donations/all".replace('//', '/')} if verbose else 1
            else:
                return {"operation": "donation", "success": False,
                        "message": "Invalid write key or not long enough"} if verbose else 0
        else:
            return {"operation": "donation", "success": False, "message": "Invalid password",
                    "hint": "Ends with " + str(official_password[-4:])} if verbose else 0

    # --------------------------------------------------------------------------
    #            Public interface  (subscription)
    # --------------------------------------------------------------------------

    def subscribe(self, name, write_key, source):
        """ Permissioned subscribe """
        return self._permissioned_subscribe_implementation(name=name, write_key=write_key, source=source)

    def msubscribe(self, name, write_key, sources):
        """ Permissioned subscribe to multiple sources """
        return self._permissioned_subscribe_implementation(name=name, write_key=write_key, sources=sources)

    def unsubscribe(self, name, write_key, source):
        return self._permissioned_unsubscribe_implementation(name=name, write_key=write_key, source=source)

    def munsubscribe(self, name, write_key, sources, delays=None):
        return self._permissioned_unsubscribe_implementation(name=name, write_key=write_key, sources=sources)

    def messages(self, name, write_key):
        """ Use key to open the mailbox """
        return self._get_messages_implementation(name=name, write_key=write_key)

    # --------------------------------------------------------------------------
    #            Public interface  (linking)
    # --------------------------------------------------------------------------

    def link(self, name, write_key, delay, target=None, targets=None):
        """ Link from a delay to one or more targets """
        return self._permissioned_link_implementation(name=name, write_key=write_key, delay=delay, target=target,
                                                      targets=targets)

    def unlink(self, name, delay, write_key, target):
        """ Permissioned removal of link (either party can do this) """
        return self._unlink_implementation(name=name, delay=delay, write_key=write_key, target=target)

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

    def _authorize(self, name, write_key):
        """ Check write_key against official records """
        return write_key == self._authority(name=name)

    def _mauthorize(self, names, write_keys):
        """ Parallel version of _authorize """
        authority = self._mauthority(names)
        assert len(names) == len(write_keys)
        comparison = [k == k1 for (k, k1) in zip(write_keys, authority)]
        return comparison

    def _authority(self, name):
        """ Returns the write_key associated with name """
        root = self._root_name(name)
        return self.client.hget(self._ownership_name(), root)

    def _mauthority(self, names, *args):
        """ Parallel version of _authority """
        names = list_or_args(names, args)
        return self.client.hmget(self._ownership_name(), *names)

    # --------------------------------------------------------------------------
    #            Implementation  (set)
    # --------------------------------------------------------------------------

    def _mset_implementation(self, names: Optional[NameList] = None, values: Optional[ValueList] = None,
                             write_keys: Optional[KeyList] = None, budgets: Optional[List[int]] = None,
                             name: Optional[str] = None, value: Optional[Any] = None, write_key: Optional[str] = None,
                             budget: Optional[int] = None,
                             return_args: Optional[List[str]] = None, with_percentiles=False, with_copulas=False):

        if return_args is None:
            return_args = ['name', 'write_key', 'value', 'percentile']
        names, values, write_keys, budgets = RedizConventions.coerce_inputs(names=names, values=values,
                                                                            write_keys=write_keys, budgets=budgets,
                                                                            name=name, value=value, write_key=write_key,
                                                                            budget=budget)
        singular = len(names) == 1

        # Convert from objects if not redis native ... this includes vectors
        values = [v if isinstance(v, (int, float, str)) else json.dumps(v) for v in values]

        # Execute assignment (creates temporary execution logs)
        execution_log = self._pipelined_set(names=names, values=values, write_keys=write_keys, budgets=budgets)

        # Ensure there is at least one baseline prediction and occasionally update it
        pools = self._pools(names, self.DELAYS)
        for nm, v, wk in zip(names, values, write_keys):
            if self.is_scalar_value(v):
                for delay_ndx, delay in enumerate(self.DELAYS):
                    if np.random.rand() < 1 / 20 or pools[nm][delay_ndx] == 0:
                        self._baseline_prediction(name=nm, value=v, write_key=wk, delay=delay)

        # Rewards, percentiles ... but only for scalar floats
        # Settlement also triggers the derived market for zscores
        if all(self.is_scalar_value(v) for v in values):
            fvalues = list(map(float, values))
            prctls = self._msettle(names=names, values=fvalues, budgets=budgets, with_percentiles=with_percentiles,
                                   write_keys=write_keys, with_copulas=with_copulas)
        else:
            prctls = None

        # Coerce execution log and maybe add percentiles
        exec_args = [arg for arg in return_args if arg in ['name', 'write_key', 'value']]
        titles = self._coerce_outputs(execution_log=execution_log, exec_args=exec_args)
        if prctls is not None:
            for title in titles:
                if title["name"] in prctls:
                    title.update({"percentiles": prctls[title["name"]]})

        # Write to confirmation log
        self._confirm(write_key=write_keys[0], operation='set', count=len(titles or []), examples=titles[:2])

        return titles[0] if singular else titles

    def _pipelined_set(self, names, values, write_keys, budgets):
        """ Parallel assignment and some knock-on effects of clearing (rewards, derived market) """
        ndxs = list(range(len(names)))
        executed_obscure, rejected_obscure, ndxs, names, values, write_keys = self._pipelined_set_obscure(ndxs=ndxs,
                                                                                                          names=names,
                                                                                                          values=values,
                                                                                                          write_keys=write_keys,
                                                                                                          budgets=budgets)
        executed_new, rejected_new, ndxs, names, values, write_keys = self._pipelined_set_new(ndxs=ndxs, names=names,
                                                                                              values=values,
                                                                                              write_keys=write_keys,
                                                                                              budgets=budgets)
        executed_existing, rejected_existing = self._pipelined_set_existing(ndxs=ndxs, names=names, values=values,
                                                                            write_keys=write_keys, budgets=budgets)
        executed = executed_obscure + executed_new + executed_existing

        # Propagate to subscribers
        modified_names = [ex["name"] for ex in executed]
        modified_values = [ex["value"] for ex in executed]
        self._propagate_to_subscribers(names=modified_names, values=modified_values)
        return {"executed": executed, "rejected": rejected_obscure + rejected_new + rejected_existing}

    @staticmethod
    def _coerce_outputs(execution_log, exec_args=None):
        """ Convert to list of dicts containing names and write keys """
        if exec_args is None:
            exec_args = ('name', 'write_key')
        sorted_log = sorted(execution_log["executed"] + execution_log["rejected"], key=lambda d: d['ndx'])
        return [dict((arg, s[arg]) for arg in exec_args) for s in sorted_log]

    def _pipelined_set_obscure(self, ndxs, names, values, write_keys, budgets):
        # Set values only if names were None. Random names will be assigned.
        executed = list()
        rejected = list()
        ignored_ndxs = list()
        if ndxs:
            obscure_pipe = self.client.pipeline(transaction=True)

            for ndx, name, value, write_key, budget in zip(ndxs, names, values, write_keys, budgets):
                if not (self.is_valid_value(value)):
                    rejected.append({"ndx": ndx, "name": name, "write_key": None, "value": value,
                                     "error": "invalid value of type " + str(type(value)) + " was supplied"})
                else:
                    if name is None:
                        if not (self.is_valid_key(write_key)):
                            rejected.append(
                                {"ndx": ndx, "name": name, "write_key": None, "errror": "invalid write_key"})
                        else:
                            new_name = self.random_name()
                            ttl = self._cost_based_ttl(value=value, budget=budget)
                            obscure_pipe, intent = self._new_obscure_page(pipe=obscure_pipe, ndx=ndx, name=new_name,
                                                                          value=value, write_key=write_key,
                                                                          budget=budget)
                            executed.append(intent)
                    elif not (self.is_valid_name(name)):
                        rejected.append({"ndx": ndx, "name": name, "write_key": None, "error": "invalid name"})
                    else:
                        ignored_ndxs.append(ndx)

            if len(executed):
                obscure_results = RedizConventions.chunker(results=obscure_pipe.execute(), n=len(executed))
                for intent, res in zip(executed, obscure_results):
                    intent.update({"result": res})

        # Marshall residual. Return indexes, names, values and write_keys that are yet to be processed.
        names = [n for n, ndx in zip(names, ndxs) if ndx in ignored_ndxs]
        values = [v for v, ndx in zip(values, ndxs) if ndx in ignored_ndxs]
        write_keys = [w for w, ndx in zip(write_keys, ndxs) if ndx in ignored_ndxs]
        return executed, rejected, ignored_ndxs, names, values, write_keys

    def _pipelined_set_new(self, ndxs, names, values, write_keys, budgets):
        # Treat cases where name does not exist yet
        executed = list()
        rejected = list()
        ignored_ndxs = list()

        if ndxs:
            exists_pipe = self.client.pipeline(transaction=False)
            fakeredis = self.client.connection is None
            for name in names:
                exists_pipe.hexists(name=self._ownership_name(), key=name)
            exists = exists_pipe.execute()

            new_pipe = self.client.pipeline(transaction=False)
            for exist, ndx, name, value, write_key, budget in zip(exists, ndxs, names, values, write_keys, budgets):
                if not (exist):
                    if not (self.is_valid_key(write_key)):
                        rejected.append({"ndx": ndx, "name": name, "write_key": None, "errror": "invalid write_key"})
                    else:
                        ttl = self._cost_based_ttl(value=value, budget=budget)
                        new_pipe, intent = self._new_page(new_pipe, ndx=ndx, name=name, value=value,
                                                          write_key=write_key, budget=budget, fakeredis=fakeredis)
                        executed.append(intent)
                else:
                    ignored_ndxs.append(ndx)

            if len(executed):
                new_results = RedizConventions.chunker(results=new_pipe.execute(), n=len(executed))
                for intent, res in zip(executed, new_results):
                    intent.update({"result": res})

        # Return those we are yet to get to because they are not new
        names = [n for n, ndx in zip(names, ndxs) if ndx in ignored_ndxs]
        values = [v for v, ndx in zip(values, ndxs) if ndx in ignored_ndxs]
        write_keys = [w for w, ndx in zip(write_keys, ndxs) if ndx in ignored_ndxs]
        return executed, rejected, ignored_ndxs, names, values, write_keys

    def _pipelined_set_existing(self, ndxs, names, values, write_keys, budgets):
        # Potentially modify existing name, assuming write_keys are correct
        executed = list()
        rejected = list()
        if ndxs:
            modify_pipe = self.client.pipeline(transaction=False)
            error_pipe = self.client.pipeline(transaction=False)
            official_write_keys = self._mauthority(names)
            for ndx, name, value, write_key, official_write_key, budget in zip(ndxs, names, values, write_keys,
                                                                               official_write_keys, budgets):
                if write_key == official_write_key:
                    modify_pipe, intent = self._modify_page(modify_pipe, ndx=ndx, name=name, value=value, budget=budget)
                    intent.update({"ndx": ndx, "write_key": write_key})
                    executed.append(intent)
                else:
                    auth_message = {"ndx": ndx, "name": name, "value": value, "write_key": write_key,
                                    "official_write_key_ends_in": official_write_key[-4:],
                                    "error": "write_key does not match page_key on record"}
                    intent = auth_message
                    error_pipe.lpush(self.errors_name(write_key=write_key), json.dumps(auth_message))
                    error_pipe.expire(self.errors_name(write_key=write_key), self.ERROR_TTL)
                    error_pipe.ltrim(name=self.errors_name(write_key=write_key), start=0, end=self.ERROR_LIMIT)
                    rejected.append(intent)
            if len(executed):
                modify_results = RedizConventions.chunker(results=modify_pipe.execute(), n=len(executed))
                for intent, res in zip(executed, modify_results):
                    intent.update({"result": res})

            if len(rejected):
                error_pipe.execute()

        return executed, rejected

    def _propagate_to_subscribers(self, names, values):
        """ Create a message for every subscriber """
        subscriber_pipe = self.client.pipeline(transaction=False)
        for name in names:
            subscriber_pipe.smembers(name=self.subscribers_name(name=name))
        subscribers_sets = subscriber_pipe.execute()
        propagate_pipe = self.client.pipeline(transaction=False)

        executed = list()
        for sender_name, value, subscribers_set in zip(names, values, subscribers_sets):
            for subscriber in subscribers_set:
                mailbox_name = self.messages_name(subscriber)
                propagate_pipe.hset(name=mailbox_name, key=sender_name, value=value)
                executed.append({"mailbox_name": mailbox_name, "sender": sender_name, "value": value})

        if len(executed):
            propagation_results = RedizConventions.chunker(results=propagate_pipe.execute(), n=len(executed))
            for intent, res in zip(executed, propagation_results):
                intent.update({"result": res})

        return executed

    def _new_obscure_page(self, pipe, ndx, name, value, write_key, budget, fakeredis=False):
        """ Almost the same as a new page """
        pipe, intent = self._new_page(pipe=pipe, ndx=ndx, name=name, value=value, write_key=write_key, budget=budget,
                                      fakeredis=fakeredis)
        intent.update({"obscure": True})
        return pipe, intent

    def _new_page(self, pipe, ndx, name, value, write_key, budget, fakeredis=False):
        """ Create new page:
              pipe         :  Redis pipeline that will be modified
            Returns also:
              intent       :  Explanation log in form of a dict
        """
        # Establish ownership
        pipe.hset(name=self._ownership_name(), key=name, value=write_key)
        pipe.sadd(self._NAMES, name)
        # Charge for stream creation
        create_charge = -budget * self._CREATE_COST
        transaction_record = {"settlement_time": str(datetime.datetime.now()), "type": "create",
                              "write_key": write_key, "amount": create_charge,
                              "message": "charge for new stream creation", "name": name}
        pipe.hincrbyfloat(name=self._BALANCES, key=write_key, amount=create_charge)
        if not fakeredis:
            log_names = [self.transactions_name(write_key=write_key),
                         self.transactions_name(write_key=write_key, name=name)]
            for ln in log_names:
                pipe.xadd(name=ln, fields=transaction_record, maxlen=self.TRANSACTIONS_LIMIT)
                pipe.expire(name=ln, time=self._TRANSACTIONS_TTL)
        # Then modify
        pipe, intent = self._modify_page(pipe=pipe, ndx=ndx, name=name, value=value, budget=budget)
        intent.update({"new": True, "write_key": write_key, "value": value})
        return pipe, intent

    def _modify_page(self, pipe, ndx, name, value, budget):
        """ Create pipelined operations for save, buffer, history etc """
        # Remark: It is important the exactly the same number of redis operations are used
        # here regardless of how things branch, because this simplifies considerably the
        # unpacking of pipelined results in calling algorithms.

        # (1) Set the actual value ... which will be overwritten by the next set() ... and a randomly named copy that survives longer
        ttl = self._cost_based_ttl(value=value, budget=budget)
        pipe.set(name=name, value=value, ex=ttl)
        name_of_copy = self._random_promised_name(name)
        promise_ttl = self._promise_ttl()
        pipe.set(name=name_of_copy, value=value, ex=promise_ttl)

        # (1.5) Update the time to live for predictions and samples
        distribution_ttl = self._cost_based_distribution_ttl(budget=budget)
        for delay in self.DELAYS:
            pipe.expire(name=self._samples_name(name=name, delay=delay), time=distribution_ttl)
            pipe.expire(name=self._sample_owners_name(name=name, delay=delay), time=distribution_ttl)
            pipe.expire(name=self._predictions_name(name=name, delay=delay), time=distribution_ttl)

        # (2) Decide how to store: lags, history or neither, but always use exactly six operations
        len_in = len(pipe)
        good_for_lags = self.is_scalar_value(value)
        if not good_for_lags:
            if self.is_small_value(value):
                if self.is_vector_value(value):
                    good_for_lags = True
        if good_for_lags:
            # Dynamically choose length of lags according to size of value
            t = time.time()
            lag_len = self._cost_based_lagged_len(value)
            lv = self.lagged_values_name(name)
            lt = self.lagged_times_name(name)
            pipe.lpush(lv, value)
            pipe.lpush(lt, t)
            pipe.ltrim(name=lv, start=0, end=lag_len)
            pipe.ltrim(name=lt, start=0, end=lag_len)
            pipe.expire(lv, ttl)
            pipe.expire(lt, ttl)

        # Other types value field(s) may be stored in stream instead ... (note again: exactly six operations so chunking of pipeline is trivial)
        if not good_for_lags:
            if self._streams_support():
                if self.is_small_value(value):
                    fields = RedizConventions.to_record(value)
                else:
                    fields = {self._POINTER: name_of_copy}
                history = self.history_name(name)
                history_len = self._cost_based_history_len(value=fields)
                pipe.xadd(history, fields=fields)
                pipe.xtrim(history, maxlen=history_len)
                pipe.expire(history, ttl)
                pipe.expire(name=name_of_copy, time=ttl)
                pipe.expire(name=name_of_copy, time=ttl)  # 5th operation
                pipe.expire(name=name_of_copy, time=ttl)  # 6th operation
            else:
                for _ in range(6):  # Again ... same hack ... insist on (6) operations here
                    pipe.expire(name=name_of_copy, time=promise_ttl)
        len_out = len(pipe)
        assert len_out - len_in == 6, "Need precisely six operations so parent function can chunk pipeline results"

        # (4) Construct delay promises
        utc_epoch_now = int(time.time())
        for delay in self.DELAYS:
            queue = self._promise_queue_name(utc_epoch_now + delay)  # self.PROMISES+str(utc_epoch_now+delay)
            destination = self.delayed_name(name=name, delay=delay)  # self.DELAYED+str(delay_seconds)+self.SEP+name
            promise = self._copy_promise(source=name_of_copy, destination=destination)
            pipe.sadd(queue, promise)
            pipe.expire(name=queue, time=promise_ttl)

        # (5) Execution log
        intent = {"ndx": ndx, "name": name, "value": value, "ttl": ttl, "new": False, "obscure": False,
                  "copy": name_of_copy}

        return pipe, intent

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

    def _delete_z1_implementation(self, names):
        """ Delete z1~, z2~ names """
        for name in names:
            znames = [self.zcurve_name(names=[name], delay=delay) for delay in self.DELAYS]
            for zname in znames:
                self._delete_implementation(zname)

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
        links_ndx = dict([(k, dict()) for k in range(len(names))])
        for name_ndx, name in enumerate(names):
            for delay_ndx, delay in enumerate(self.DELAYS):
                links_ndx[name_ndx][delay_ndx] = len(info_pipe)
                info_pipe.hgetall(self.links_name(name=name, delay=delay))

        info_exec = info_pipe.execute()
        assert len(info_exec) == 3 * len(names) + len(names) * len(self.DELAYS)
        subscribers_res = info_exec[:len(names)]
        subscriptions_res = info_exec[len(names):2 * len(names)]
        backlinks_res = info_exec[2 * len(names):]

        # (b)   Second call will do all remaining cleanup
        delete_pipe = self.client.pipeline(transaction=False)

        # (b-1) Force backlinkers to unlink
        for name, backlinks in zip(names, backlinks_res):
            for backlink in list(backlinks.keys()):
                root, delay = self._interpret_delay(backlink)
                delete_pipe = self._unlink_pipe(pipe=delete_pipe, name=root, delay=int(delay), target=name)

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
                targets = list(info_exec[link_ndx].keys())
                if targets:
                    for target in targets:
                        delete_pipe = self._unlink_pipe(pipe=delete_pipe, name=name, delay=delay, target=target)

        # (b-5) Then discard derived ... delete can be slow so we expire instead
        for name in names:
            derived_names = list(self.derived_names(name).values()) + list(self._private_derived_names(name).values())
            for derived_name in derived_names:
                delete_pipe.pexpire(name=derived_name, time=1)

        # (b-7) Delete budget
        delete_pipe.hdel(self.BUDGETS, *names)
        delete_pipe.hdel(self.VOLUMES, *names)

        # (b-6) And de-register the name
        delete_pipe.srem(self._NAMES, *names)
        delete_pipe.hdel(self._ownership_name(), *names)

        del_exec = delete_pipe.execute()

        return sum((1 for r in del_exec if r))

    # --------------------------------------------------------------------------
    #            Implementation  (touch)
    # --------------------------------------------------------------------------

    def _sanitize_log_entry(self, s):
        return s.replace(self._obscurity, 'OBSCURE')

    def _log_to_list(self, log_name, ttl, limit, data=None, **kwargs):
        """ Append to list style log """
        log_entry = {'time': str(datetime.datetime.now()), 'epoch_time': time.time()}
        if data:
            log_entry.update(data)
        log_entry.update(**kwargs)
        logging_pipe = self.client.pipeline(transaction=False)
        logging_pipe.lpush(log_name, self._sanitize_log_entry(json.dumps(log_entry)))
        logging_pipe.expire(log_name, ttl)
        logging_pipe.ltrim(log_name, start=0, end=limit)
        logging_pipe.execute(raise_on_error=True)

    def _confirm(self, write_key, data=None, **kwargs):
        self._log_to_list(log_name=self.confirms_name(write_key=write_key), ttl=self.CONFIRMS_TTL,
                          limit=self.CONFIRMS_LIMIT, data=data, **kwargs)

    def _error(self, write_key, data=None, **kwargs):
        self._log_to_list(log_name=self.errors_name(write_key=write_key), ttl=self.ERROR_TTL,
                          limit=self.ERROR_LIMIT, data=data, **kwargs)

    def _warn(self, write_key, data=None, **kwargs):
        self._log_to_list(log_name=self.warnings_name(write_key=write_key), ttl=self.WARNINGS_TTL,
                          limit=self.WARNINGS_LIMIT, data=data, **kwargs)

    def _touch_implementation(self, name, write_key, budget, example_value=3.145):
        """ Extend life of stream """
        exec = self.client.expire(name=name, time=self._cost_based_ttl(value=example_value, budget=budget))
        self._confirm(write_key=write_key, operation='touch', name=name, execution=exec)
        if not exec:
            self._warn(write_key=write_key, operation='touch', error='expiry not set ... names may not exist',
                       name=name, exec=exec)
        return exec

    def _mtouch_implementation(self, names, write_key, budgets, example_value=3.145):
        """ Extend life of multiple streams """
        ttls = [self._cost_based_ttl(value=example_value, budget=b) for b in budgets]

        expire_pipe = self.client.pipeline()
        for name, ttl in zip(names, ttls):
            dn = self.derived_names(name=name)
            pdn = self._private_derived_names(name=name)
            all_names = [name] + list(dn.values()) + list(pdn.values())
            for nm in all_names:
                expire_pipe.expire(name=nm, time=ttl)
        exec = expire_pipe.execute()
        report = dict(zip(all_names, exec))
        self._confirm(write_key=write_key, operation='mtouch', count=sum(exec))
        if not any(exec):
            self._warn(write_key=write_key, operation='mtouch', error='expiry not set ... names may not exist',
                       data=report, ttls=ttls)
        return sum(exec)

    def _copula_touch_implementation(self, names, budgets):
        return False  # TODO

    # --------------------------------------------------------------------------
    #            Implementation  (subscribe)
    # --------------------------------------------------------------------------

    def _permissioned_subscribe_implementation(self, name, write_key, source=None, sources: Optional[NameList] = None):
        """ Permissioned subscribe to one or more sources """
        if self._authorize(name=name, write_key=write_key):
            return self._subscribe_implementation(name=name, source=source, sources=sources)

    def _subscribe_implementation(self, name, source=None, sources=None):
        if source or sources:
            sources = sources or [source]
            the_pipe = self.client.pipeline()
            for _source in sources:
                the_pipe.sadd(self.subscribers_name(_source), name)
            the_pipe.sadd(self.subscriptions_name(name), *sources)
            exec = the_pipe.execute()
            return sum(exec) / 2
        else:
            return 0

    def _unsubscribe_pipe(self, pipe, name, source=None, sources=None):
        if source or sources:
            sources = sources or [source]
            for _source in sources:
                if _source is not None:
                    pipe.srem(self.subscribers_name(_source), name)
            if self._INSTANT_RECALL:
                pipe.hdel(self.messages_name(name), sources)
            pipe.srem(self.subscriptions_name(name), *sources)
        return pipe

    def _permissioned_unsubscribe_implementation(self, name, write_key, source=None,
                                                 sources: Optional[NameList] = None):
        """ Permissioned unsubscribe from one or more sources """
        if self._authorize(name=name, write_key=write_key):
            pipe = self.client.pipeline()
            pipe = self._unsubscribe_pipe(pipe=pipe, name=name, source=source, sources=sources)
            exec = pipe.execute()
            return sum(exec)
        else:
            return 0

    def _get_messages_implementation(self, name, write_key):
        if self._authorize(name=name, write_key=write_key):
            return self.client.hgetall(self.MESSAGES + name)

    # --------------------------------------------------------------------------
    #            Implementation  (linking)
    # --------------------------------------------------------------------------

    def _root_name(self, name):
        return name.split(self.SEP)[-1]

    def _permissioned_link_implementation(self, name, write_key, delay, target=None, targets=None):
        " Create link to possibly non-existent target(s) "
        # TODO: Maybe optimize with a beg for forgiveness patten to avoid two calls
        if targets is None:
            targets = [target]
        root = self._root_name(name)
        assert root == name, " Supply root name and a delay "
        target_root = self._root_name(target)
        assert target == target_root
        if self._authorize(name=root, write_key=write_key):
            link_pipe = self.client.pipeline()
            link_pipe.exists(*targets)
            edge_weight = 1.0  # May change in the future
            for target in targets:
                link_pipe.hset(self.links_name(name=name, delay=delay), key=target, value=edge_weight)
                link_pipe.hset(self.backlinks_name(name=target), key=self.delayed_name(name=name, delay=delay),
                               value=edge_weight)
            exec = link_pipe.execute()
            return sum(exec) / 2
        else:
            return 0

    def _unlink_implementation(self, name, delay, write_key, target):
        # Either party can unlink
        if self._authorize(name=name, write_key=write_key) or self._authorize(name=target, write_key=write_key):
            pipe = self.client.pipeline(transaction=True)
            pipe = self._unlink_pipe(pipe=pipe, name=name, delay=delay, target=target)
            exec = pipe.execute()
            return exec

    def _unlink_pipe(self, pipe, name, delay, target):
        pipe.hdel(self.links_name(name, delay), target)
        pipe.hdel(self.backlinks_name(target), self.delayed_name(name=name, delay=delay))
        return pipe

    # --------------------------------------------------------------------------
    #      Implementation  (Admministrative - garbage collection )
    # --------------------------------------------------------------------------

    def _transfer_implementation(self, source_write_key, recipient_write_key, amount, as_record=False):
        """ Debit and credit write_keys """
        transfer_confirm = {"time": str(datetime.datetime.now()), "operation": "transfer", "epoch_time": time.time(),
                            "source": self.shash(source_write_key), "recipient": self.shash(recipient_write_key)}
        success = 0
        if self.is_valid_key(source_write_key) and self.key_difficulty(source_write_key) >= self.MIN_LEN - 1:
            if self.is_valid_key(recipient_write_key):
                recipient_balance = self.get_balance(write_key=recipient_write_key)
                if recipient_balance < -1.0:
                    source_distance = self.distance_to_bankruptcy(source_write_key)
                    maximum_to_receive = -recipient_balance  # Cannot make a balance positive
                    maximum_to_give = max(0, source_distance)
                    if amount is None:
                        amount = maximum_to_give
                    given = min([maximum_to_give, maximum_to_receive, amount])
                    received = given * self._DISCOUNT
                    transfer_confirm.update(
                        {'max_to_give': maximum_to_give, 'max_to_receive': maximum_to_receive, 'given': given,
                         'received': received})
                    if given > 0.1:
                        pipe = self.client.pipeline(transaction=True)
                        pipe.hincrbyfloat(name=self._BALANCES, key=source_write_key, amount=-given)
                        pipe.hincrbyfloat(name=self._BALANCES, key=recipient_write_key, amount=received)
                        execut = pipe.execute()
                        success = 1
                    else:
                        transfer_confirm.update(
                            {'reason': 'Not in a position to give, or not in a position to receive'})
                else:
                    transfer_confirm.update({"reason": "Cannot transfer to a key balance above -1.0"})
            else:
                transfer_confirm.update({"reason": "Invalid recipient write_key"})
        else:
            transfer_confirm.update(
                {"reason": "Invalid source write_key, must be " + str(self.MIN_LEN - 1) + " difficulty."})

        # Logging confirms
        transfer_confirm.update({"success": success})
        self._confirm(write_key=source_write_key, data=transfer_confirm)
        self._confirm(write_key=recipient_write_key, data=transfer_confirm)
        return success if not as_record else transfer_confirm

    def bankruptcy(self, write_key_len):
        if write_key_len <= 8:
            return -0.01
        return -1.0 * (abs(self.min_balance) * (16 ** (write_key_len - 9)))

    def bankrupt(self, write_key):
        return self.distance_to_bankruptcy(write_key=write_key) < 0

    def distance_to_bankruptcy(self, write_key):
        level = self.bankruptcy(self.key_difficulty(write_key))
        balance = self.get_balance(write_key=write_key)
        return balance - level

    def admin_bankruptcy(self, with_report=False):
        """
            Force cancellations when owners of predictions are bankrupt
        """
        name = self.client.srandmember(self._NAMES)
        discards = list()
        for delay in self.DELAYS:
            write_keys = self._get_sample_owners(name, delay)
            leaderboard = self._get_leaderboard_implementation(name=name, delay=delay, readable=False, count=10000)
            losers = [key for key in write_keys if
                      (self.shash(key) in leaderboard) and (leaderboard[self.shash(key)] < -1.0)]

            for write_key in losers:
                if self.bankrupt(write_key=write_key):
                    self._confirm(write_key=write_key,
                                  data={"operation": "bankruptcy", "time": str(datetime.datetime.now()),
                                        "epoch_time": time.time(), "name": name, "code": self.shash(write_key)})
                    self.cancel(name=name, write_key=write_key, delay=delay)
                    discards.append((name, write_key))
        return len(discards) if not with_report else {"discards": discards}

    def admin_garbage_collection(self, fraction=0.1, with_report=False):
        """ Randomized search and destroy for expired data """
        num_keys = self.client.scard(self._NAMES)
        num_survey = min(100, max(20, int(fraction * num_keys)))
        orphans = self._randomly_find_orphans(num=num_survey)
        if orphans is not None:
            self._delete_implementation(*orphans)
            return len(orphans) if not with_report else {"ophans": orphans}
        else:
            return 0 if not with_report else {"orphans": None}

    def _randomly_find_orphans(self, num=1000):
        NAMES = self._NAMES
        unique_random_names = list(set(self.client.srandmember(NAMES, num)))
        num_random = len(unique_random_names)
        if num_random:
            num_exists = self.client.exists(*unique_random_names)
            if num_exists < num_random:
                # There must be orphans, defined as those who are listed
                # in reserved["names"] but have expired
                exists_pipe = self.client.pipeline(transaction=True)
                for name in unique_random_names:
                    exists_pipe.exists(name)
                exists = exists_pipe.execute()

                orphans = [name for name, ex in zip(unique_random_names, exists) if not (ex)]
                return orphans

    # --------------------------------------------------------------------------
    #            Implementation  (Administrative - promises)
    # --------------------------------------------------------------------------

    def _cancellation_rounded_time(self, t):
        return int(round(t, -2))

    def admin_cancellations(self, with_report=False):
        """
              Look at queues of requests to cancel predictions, and process them
        """

        # Find recent cancellation queues that exist
        exists_pipe = self.client.pipeline()
        utc_epoch_now = int(time.time())
        candidates = list(set(
            [self._cancellation_queue_name(epoch_seconds=self._cancellation_rounded_time(utc_epoch_now - seconds)) for
             seconds in range(self._CANCEL_GRACE, -1, -1)]))
        for candidate in candidates:
            exists_pipe.exists(candidate)
        exists = exists_pipe.execute()

        # Get them if they exist
        get_pipe = self.client.pipeline()
        cancellation_queue_name = [promise for promise, exist in zip(candidates, exists) if exists]
        for collection_name in cancellation_queue_name:
            get_pipe.smembers(collection_name)
        collections = get_pipe.execute()
        self.client.delete(*cancellation_queue_name)

        # Perform cancellations
        individual_cancellations = list(itertools.chain(*collections))
        for cancellation in individual_cancellations:
            if self.CANCEL_SEP in cancellation:
                write_key, horizon = cancellation.split(self.CANCEL_SEP)
                name, delay = self.split_horizon_name(horizon)
                self._delete_scenarios_implementation(name=name, write_key=write_key, delay=delay)

        return sum(individual_cancellations) if not with_report else {'cancellations': individual_cancellations}

    def admin_promises(self, with_report=False):
        """ Iterate through task queues populating delays and samples """

        # Find recent promise queues that exist
        exists_pipe = self.client.pipeline()
        utc_epoch_now = int(time.time())
        candidates = [self._promise_queue_name(epoch_seconds=utc_epoch_now - seconds) for seconds in
                      range(self._DELAY_GRACE, -1, -1)]
        for candidate in candidates:
            exists_pipe.exists(candidate)
        exists = exists_pipe.execute()

        # If they exist get the members
        get_pipe = self.client.pipeline()
        promise_collection_names = [promise for promise, exist in zip(candidates, exists) if exists]
        for collection_name in promise_collection_names:
            get_pipe.smembers(collection_name)
        collections = get_pipe.execute()
        self.client.delete(
            *promise_collection_names)  # Immediately delete task list so it isn't done twice ... not that that would
        # be the end of the world
        individual_promises = list(itertools.chain(*collections))

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

        sources = list(dest_source.values())
        destinations = list(dest_source.keys())
        methods = list(dest_method.values())

        # Interpret the promises as source / destination references and get the source values
        retrieve_pipe = self.client.pipeline()
        for source, destination, method in zip(sources, destinations, methods):
            if method == 'copy':
                retrieve_pipe.get(source)
            elif method == 'predict':
                retrieve_pipe.zrange(name=source, start=0, end=-1, withscores=True)
            elif method == 'cancel':
                retrieve_pipe.get(source)
        source_values = retrieve_pipe.execute()

        # Copy delay promises and insert prediction promises
        move_pipe = self.client.pipeline(transaction=False)
        report = dict()
        report['warnings'] = ''
        execution_report = list()
        for value, destination, method in zip(source_values, destinations, methods):
            if method == 'copy':
                if value is None:
                    report['warnings'] = report['warnings'] + ' None value found '
                else:
                    delay_ttl = int(max(self.DELAYS) + self._DELAY_GRACE + 5 * 60)
                    move_pipe.set(name=destination, value=value, ex=delay_ttl)
                    execution_report.append({"operation": "set", "destination": destination, "value": value})
                    report[destination] = str(value)
            elif method == 'predict':
                if len(value):
                    value_as_dict = dict(value)
                    move_pipe.zadd(name=destination, mapping=value_as_dict, ch=True)
                    execution_report.append(
                        {"operation": "zadd", "destination": destination, "len": len(value_as_dict)})
                    report[destination] = str(len(value_as_dict))
                    owners = [self._scenario_owner(ticket) for ticket in value_as_dict.keys()]
                    unique_owners = list(set(owners))
                    try:
                        move_pipe.sadd(self._OWNERS + destination, *unique_owners)
                        execution_report.append(
                            {"operation": "sadd", "destination": self._OWNERS + destination, "value": unique_owners})
                    except DataError:
                        report[destination] = "Failed to insert predictions to " + destination
            else:
                raise Exception("bug - missing case ")

        execut = move_pipe.execute()
        for record, ex in zip(execution_report, execut):
            record.update({"execution_result": ex})

        return sum(execut) if not with_report else execution_report

    # --------------------------------------------------------------------------
    #            Implementation  (prediction and settlement)
    # --------------------------------------------------------------------------

    def _baseline_prediction(self, name, value, write_key, delay):
        # As a finer point, we should really be using the delay times here and sampling by time not lag ... but it is just a lazy benchmark anyway
        lagged_values = self._get_lagged_implementation(name, with_times=False, with_values=True, to_float=True,
                                                        start=0, end=None, count=self.num_predictions)
        predictions = self.empirical_predictions(lagged_values=lagged_values)
        return self._set_scenarios_implementation(name=name, values=predictions, write_key=write_key, delay=delay)

    def _cancel_implementation(self, name, write_key, delay=None, delays=None):
        """
            Cancellation cannot occur immediately, as that would allow sneaky people to put in predictions and
            then cancel them later when it seems that they might not perform well.

            Instead, a promise to cancel is created.

            Later, the actual cancellation will occur.

        :param name:         stream name
        :param write_key:
        :param delay:        int
        :param delays:       [ int ]
        :return:
        """
        if delays is None and delay is None:
            delays = self.DELAYS
        elif delays is None:
            delays = [delay]
        assert name == self._root_name(name)
        utc_epoch_now = time.time()
        pipe = self.client.pipeline()
        cancel_queues = list()
        if self.is_valid_key(write_key):
            for delay_seconds in delays:
                cancel_queue = self._cancellation_queue_name(
                    self._cancellation_rounded_time(utc_epoch_now + delay_seconds))
                cancellation = self._cancellation_promise(name=name, delay=delay_seconds, write_key=write_key)
                pipe.sadd(cancel_queue, cancellation)  # (3::3)
                pipe.expire(name=cancel_queue, time=delay_seconds + 10 * self._DELAY_GRACE)
                cancel_queues.append(cancel_queue)
            exec = pipe.execute()
            DEBUG = True
            if DEBUG:
                retrieved = self.client.smembers(cancel_queues[0])
                pprint(cancel_queues)
            expected_exec = [1, True] * len(delays)
            success = all([e1 == e2 for e1, e2 in zip(exec, expected_exec)])
            confirmation = {'operation': 'withdraw', 'time': str(datetime.datetime.now()), 'name': name,
                            'delays': delays, 'success': success, 'code': self.shash(write_key),
                            'epoch_time': time.time()}
            self._confirm(write_key=write_key, data=confirmation)

            return 1 if all(exec) else 0
        return 0

    def _delete_scenarios_implementation(self, name, write_key, delay=None, delays=None):
        """ Second phase of cancellation
              This is instantaneous deletion ... it is called by the admin when promises to delete are found at the right time.
        """
        if delays is None and delay is None:
            delays = self.DELAYS
        elif delays is None:
            delays = [delay]
        assert name == self._root_name(name)
        if self.is_valid_key(write_key) and all(d in self.DELAYS for d in delays):
            delete_pipe = self.client.pipeline(
                transaction=True)  # <-- Important that transaction=True lest submissions and owners get out of sync
            code = self.animal_from_key(write_key)
            confirmation = {'operation': 'cancel', 'time': str(datetime.datetime.now()), 'success': True, 'name': name,
                            'delays': delays, 'participant': code, 'epoch_time': time.time(),
                            'explanation': 'delayed withdrawal is complete'}
            for delay in delays:
                collective_predictions_name = self._predictions_name(name, delay)
                keys = [self._format_scenario(write_key, k) for k in range(self.num_predictions)]
                delete_pipe.zrem(collective_predictions_name, *keys)  # 1000
                samples_name = self._samples_name(name=name, delay=delay)
                delete_pipe.zrem(samples_name, *keys)  # 1000
                owners_name = self._sample_owners_name(name=name, delay=delay)
                delete_pipe.srem(owners_name, write_key)  # 1
            _execut = delete_pipe.execute()

            confirmation.update({'execute': _execut})

            self._confirm(write_key=write_key, data=confirmation)

    def _get_scenarios_implementation(self, name, write_key, delay, cursor=0):
        """ Charge for this! Not encouraged as it should not be necessary, and it is inefficient to get scenarios back from the collective zset """
        assert name == self._root_name(name)
        if self.is_valid_key(write_key) and delay in self.DELAYS:
            cursor, items = self.client.zscan(name=self._predictions_name(name=name, delay=delay), cursor=cursor,
                                              match='*' + write_key + '*', count=self.num_predictions)
            return {"cursor": cursor, "scenarios": dict(items)}

    def _get_invcdf_implementation(self, name, delay, percentiles):
        """ Random estimate of invcdf at percentiles 0 < p < 1 """
        # Requires maintenance of a sketch which is left for future work
        # A hack is provided in the client library for now
        raise NotImplementedError()

    def _get_cdf_implementation(self, name, delay, values, top, min_balance):
        """" Possibly we need to split logic into continuous and discrete cases :( """
        assert name == self._root_name(name), "get_cdf expects root name"
        assert delay in self.DELAYS, "delay is not a valid choice of delay"

        score_pipe = self.client.pipeline()
        num = self.client.zcard(name=self._predictions_name(name=name, delay=delay))
        lb = self._get_leaderboard_implementation(name=name, delay=delay, readable=False, count=top)
        included = [write_key for write_key, balance in lb.items() if balance > min_balance]
        if num:
            h = min(0.1, max(5.0 / num, 0.00001)) * max([abs(v) for v in values] + [1.0])
            for value in values:
                score_pipe.zrevrangebyscore(name=self._predictions_name(name=name, delay=delay), max=value,
                                            min=value - h, start=0, num=5, withscores=False)
                score_pipe.zrangebyscore(name=self._predictions_name(name=name, delay=delay), min=value,
                                         max=value + h, start=0, num=5, withscores=False)

            execut = score_pipe.execute()
            execut_combined = RedizConventions.chunker(execut, n=len(values))
            execut_merged = [lst[0] + lst[1] for lst in execut_combined]
            prtcls = [
                self._zmean_scenarios_percentile(percentile_scenarios=ex, included_codes=included) if ex else np.NaN for
                ex in execut_merged]
            valid = [(v, p) for v, p in zip(values, prtcls) if not np.isnan(p) and abs(p - 0.5) > 1e-6]

            # Make CDF monotone using avg of min and max envelopes running from each direction
            ys1 = [p for v, p in valid]
            ys2 = list(reversed([p for v, p in valid]))
            xs = [v for v, p in valid]
            if ys1:
                ys_monotone_1 = list(np.maximum.accumulate(np.array(ys1)))
                ys_monotone_2 = list(np.minimum.accumulate(np.array(ys2)))
                ys_monotone = [0.5 * (y1 + y2) for y1, y2 in zip(ys_monotone_1, reversed(ys_monotone_2))]
                return {"x": xs, "y": ys_monotone}
            else:
                return {"x": xs, "y": ys1}
        else:
            return {"message": "No predictions."}

    def _set_scenarios_implementation(self, name, values, write_key, delay=None, delays=None, verbose=False):
        """ Supply scenarios """
        if delays is None and delay is None:
            delays = self.DELAYS
        elif delays is None:
            delays = [delay]
        assert name == self._root_name(name)
        if len(values) == self.num_predictions and self.is_valid_key(write_key
                                                                     ) and all(
            [isinstance(v, (int, float)) for v in values]) and all(delay in self.DELAYS for delay in delays):
            # Ensure sorted ... TODO: force this on the algorithm, or charge a fee?
            values = sorted(values)

            # Jigger sorted predictions
            noise = np.random.randn(self.num_predictions).tolist()
            jiggered_values = [v + n * self.NOISE for v, n in zip(values, noise)]
            jiggered_values.sort()
            if  len(set(jiggered_values)) != len(jiggered_values):
                print('----- submission error ----- ')
                num_unique = len(set(values))
                num_jiggled_unique = len(set(values))
                if False:
                    print('Values...')
                    pprint(values)
                    print('Jigged values ...')
                    pprint(jiggered_values)
                error_message = "Cannot accept submission as there are "+str(num_unique)+" unique values ("+str(num_jiggled_unique)+" unique after noise added)"
                print(error_message,flush=True)
                raise Exception(error_message)
            predictions = dict(
                [(self._format_scenario(write_key=write_key, k=k), v) for k, v in enumerate(jiggered_values)])

            # Open pipeline
            set_and_expire_pipe = self.client.pipeline()

            # Add to collective contemporaneous forward predictions
            for delay in delays:
                collective_predictions_name = self._predictions_name(name, delay)
                set_and_expire_pipe.zadd(name=collective_predictions_name, mapping=predictions, ch=True,
                                         nx=False)  # [num]*len(delays)

            # Create obscure predictions and promise to insert them later, at different times, into different samples
            utc_epoch_now = int(time.time())
            individual_predictions_name = self._random_promised_name(name)
            set_and_expire_pipe.zadd(name=individual_predictions_name, mapping=predictions, ch=True)  # num
            promise_ttl = max(self.DELAYS) + self._DELAY_GRACE
            set_and_expire_pipe.expire(name=individual_predictions_name, time=promise_ttl)  # true
            for delay_seconds in delays:
                promise_queue = self._promise_queue_name(utc_epoch_now + delay_seconds)
                promise = self._prediction_promise(target=name, delay=delay_seconds,
                                                   predictions_name=individual_predictions_name)
                set_and_expire_pipe.sadd(promise_queue, promise)  # (3::3)
                set_and_expire_pipe.expire(name=promise_queue, time=delay_seconds + self._DELAY_GRACE)  # (4::3)
                set_and_expire_pipe.expire(name=individual_predictions_name,
                                           time=delay_seconds + self._DELAY_GRACE)  # (5::3)

            # Execute pipeline ... should not fail (!)
            execut = set_and_expire_pipe.execute()
            anticipated_execut = [self.num_predictions] * len(delays) + [self.num_predictions, True] + [1, True,
                                                                                                        True] * len(
                delays)

            def _close(a1, a2):
                return a1 == a2 or (isinstance(a1, int) and a1 > 20 and ((a1 - a2) / self.num_predictions) < 0.05)

            success = all(
                _close(actual, anticipate) for actual, anticipate in itertools.zip_longest(execut, anticipated_execut))
            warn = not (all(a1 == a2) for a1, a2 in itertools.zip_longest(execut, anticipated_execut))

            confirmation = {'write_key': write_key, 'operation': 'submit', 'name': name, 'delays': delays,
                            'some_values': values[:5], 'success': success, 'warn': warn}
            if success:
                self._confirm(**confirmation)
            if not success or warn:
                confirmation.update({'antipated_execut': anticipated_execut, 'actual_execut': execut})
                self._error(**confirmation)

            return confirmation if verbose else success
        else:
            # TODO: Log failed prediction attempt to write_key log
            return 0

    def _msettle(self, names, values, budgets, with_percentiles, write_keys, with_copulas):
        """ Parallel version of settle  """

        half_winners = int(math.ceil(self.NUM_WINNERS))

        assert len(set(names)) == len(names), "mget() cannot be used with repeated names"
        retrieve_pipe = self.client.pipeline()
        num_delay = len(self.DELAYS)
        num_windows = len(self._WINDOWS)
        sponsors = [self.shash(ky) for ky in write_keys]

        # ----  Construct pipe to retrieve quarantined predictions ----------
        scenarios_lookup = dict(
            [(name, dict([(delay_ndx, dict()) for delay_ndx in range(num_delay)])) for name in names])
        pools_lookup = dict([(name, dict()) for name in names])
        participants_lookup = dict([(name, dict()) for name in names])
        for name, value in zip(names, values):
            for delay_ndx, delay in enumerate(self.DELAYS):
                samples_name = self._samples_name(name=name, delay=delay)
                pools_lookup[name][delay_ndx] = len(retrieve_pipe)
                retrieve_pipe.zcard(samples_name)  # Total number of entries
                participants_lookup[name][delay_ndx] = len(retrieve_pipe)
                retrieve_pipe.smembers(self._sample_owners_name(name=name, delay=delay))  # List of owners
                for window_ndx, window in enumerate(self._WINDOWS):
                    scenarios_lookup[name][delay_ndx][window_ndx] = len(retrieve_pipe)
                    retrieve_pipe.zrangebyscore(name=samples_name, min=value, max=value + 0.5 * window,
                                                withscores=False, start=0, num=half_winners)
                    retrieve_pipe.zrevrangebyscore(name=samples_name, max=value, min=value - 0.5 * window,
                                                   withscores=False, start=0, num=half_winners)
        retrieved = retrieve_pipe.execute()

        # ---- Compute percentiles by zooming out until we have enough points ---
        some_percentiles = False
        percentiles = dict([(name, dict((d, 0.5) for d in range(len(self.DELAYS)))) for name in names])
        if with_percentiles:
            for name in names:
                pools = [retrieved[pools_lookup[name][delay_ndx]] for delay_ndx in range(num_delay)]
                if any(pools):
                    for delay_ndx, pool in enumerate(pools):
                        assert pool == retrieved[pools_lookup[name][delay_ndx]]  # Just checkin
                        participant_set = retrieved[participants_lookup[name][delay_ndx]]
                        if pool and len(participant_set) >= 1:
                            # Zoom out window for percentiles ... want a few so we can average zscores
                            # from more than one contributor, hopefully leading to more accurate percentiles
                            percentile_scenarios = list()
                            for window_ndx in range(num_windows):
                                if len(percentile_scenarios) < 10:
                                    _ndx = scenarios_lookup[name][delay_ndx][window_ndx]
                                    percentile_scenarios_up = retrieved[_ndx]
                                    percentile_scenarios_dn = retrieved[_ndx + 1]
                                    percentile_scenarios = percentile_scenarios_dn + percentile_scenarios_up
                                    some_percentiles = len(percentile_scenarios) > 0
                            percentiles[name][delay_ndx] = self._zmean_scenarios_percentile(
                                percentile_scenarios=percentile_scenarios)

        # ---- Rewards and leaderboard update pipeline
        pipe = self.client.pipeline()
        pipe.hmset(name=self.BUDGETS, mapping=dict(zip(names, budgets)))  # Log the budget decision
        for name, budget, write_key, sponsor, value in zip(names, budgets, write_keys, sponsors, values):
            pools = [retrieved[pools_lookup[name][delay_ndx]] for delay_ndx in range(num_delay)]
            if any(pools):
                participant_sets = [retrieved[participants_lookup[name][delay_ndx]] for delay_ndx in range(num_delay)]
                for delay_ndx, delay, pool, participant_set in zip(range(num_delay), self.DELAYS, pools,
                                                                   participant_sets):
                    payments = Counter()
                    if pool and len(participant_set) > 1:
                        # Zoom out rewards scenarios window if we don't have a winner
                        # Possibly this should be adjusted by the number of participants to reduce wealth variance
                        # It is unlikely that we'd have just one so won't worry too much about this for now.
                        rewarded_scenarios = list()
                        for window_ndx in range(num_windows):
                            if len(rewarded_scenarios) == 0:
                                _ndx = scenarios_lookup[name][delay_ndx][window_ndx]
                                rewarded_scenarios = retrieved[_ndx]
                                winning_window_ndx = window_ndx
                        winning_window = self._WINDOWS[winning_window_ndx]
                        num_rewarded = len(rewarded_scenarios)

                        game_payments = self._game_payments(pool=pool, participant_set=participant_set,
                                                            rewarded_scenarios=rewarded_scenarios)
                        payments.update(game_payments)

                    if len(payments):
                        leaderboard_names = [self.leaderboard_name(),
                                             self.leaderboard_name(name=name),
                                             self.leaderboard_name(name=None, delay=delay),
                                             self.leaderboard_name(name=name, delay=delay),
                                             self.custom_leaderboard_name(sponsor=None, name=None),  # Overall all time
                                             self.custom_leaderboard_name(sponsor=None, name=None,
                                                                          dt=datetime.datetime.now()),  # This month
                                             self.custom_leaderboard_name(sponsor=sponsor, name=None),
                                             # Sponsor category
                                             self.custom_leaderboard_name(sponsor=sponsor, name=name),
                                             # Sponsor and cateogry
                                             self.custom_leaderboard_name(sponsor=sponsor, dt=datetime.datetime.now()),
                                             # Sponsor and month
                                             self.custom_leaderboard_name(sponsor=sponsor, name=name,
                                                                          dt=datetime.datetime.now()),
                                             # Sponsor and category and month
                                             self.custom_leaderboard_name(sponsor=sponsor, name=name,
                                                                          dt=datetime.datetime.now())
                                             ]
                        for (recipient, amount) in payments.items():
                            # Record keeping
                            rescaled_amount = budget * float(amount)
                            pipe.hincrbyfloat(name=self._BALANCES, key=recipient, amount=rescaled_amount)
                            pipe.hincrbyfloat(name=self.VOLUMES, key=self.horizon_name(name=name, delay=delay),
                                              amount=abs(rescaled_amount))
                            write_code = self.shash(write_key)
                            recipient_code = self.shash(recipient)
                            # Leaderboards
                            for lb in leaderboard_names:
                                pipe.zincrby(name=lb, value=recipient_code, amount=rescaled_amount)
                            # Performance
                            pipe.hincrbyfloat(name=self.performance_name(write_key=recipient),
                                              key=self.horizon_name(name=name, delay=delay), amount=rescaled_amount)
                            # Transactions logs:
                            maxed_out = num_rewarded == 2 * half_winners
                            mass = num_rewarded / pool if pool > 0.0 else 0.
                            density = mass / winning_window
                            reliable = 0 if maxed_out else 1
                            breakeven = self.num_predictions*num_rewarded/pool if pool>0 else 0

                            transaction_record = {"settlement_time": str(datetime.datetime.now()),
                                                  "amount": rescaled_amount,
                                                  "budget": budget,
                                                  "stream": name,
                                                  "delay": delay,
                                                  "value": value,
                                                  "window": winning_window,
                                                  "mass": mass,
                                                  "density": density,
                                                  "average": breakeven,
                                                  "reliable": reliable,
                                                  "submissions_count": pool,
                                                  "submissions_close": num_rewarded,
                                                  "stream_owner_code": write_code,
                                                  "recipient_code": recipient_code}
                            log_names = [self.transactions_name(),
                                         self.transactions_name(write_key=recipient),
                                         self.transactions_name(write_key=recipient, name=name),
                                         self.transactions_name(write_key=recipient, name=name, delay=delay)]
                            for ln in log_names:
                                pipe.xadd(name=ln, fields=transaction_record, maxlen=self.TRANSACTIONS_LIMIT)
                                pipe.expire(name=ln, time=self._TRANSACTIONS_TTL)
                        for lb in leaderboard_names:
                            pipe.expire(name=lb, time=self._LEADERBOARD_TTL)

        settle_exec = pipe.execute()  # No checks here

        if with_percentiles and some_percentiles:
            first_write_key = write_keys[0]
            # Derived markets use 1-d, 2-d, 3-d market-implied z-scores and z-curves
            z_budgets = list()
            z_names = list()
            z_curves = list()
            z_write_keys = list()
            for delay_ndx, delay in enumerate(self.ZDELAYS):
                percentiles1 = [percentiles[name][delay_ndx] for name in names]
                legit = not (all([abs(p1 - 0.5) < 1e-5 for p1 in percentiles1]))
                if legit:
                    num_names = len(names)
                    selections = list(itertools.combinations(list(range(num_names)), 1))
                    if with_copulas and num_names <= 10:
                        selections2 = list(itertools.combinations(list(range(num_names)), 2))
                        selections3 = list(itertools.combinations(list(range(num_names)), 3))
                        selections = selections + selections2 + selections3

                    for selection in selections:
                        selected_names = [names[o] for o in selection]
                        dim = len(selection)
                        z_budget = sum([budgets[o] for o in selection]) / (10 * dim)  # FIXME: Why int?
                        selected_prctls = [percentiles1[o] for o in selection]
                        zcurve_value = self.to_zcurve(selected_prctls)
                        zname = self.zcurve_name(selected_names, delay)
                        z_names.append(zname)
                        z_budgets.append(z_budget)
                        z_curves.append(zcurve_value)
                        z_write_keys.append(first_write_key)
            if z_names:
                self._mset_implementation(budgets=z_budgets, names=z_names, values=z_curves, write_keys=z_write_keys,
                                          with_percentiles=False, with_copulas=False)
        return percentiles

    def _zmean_scenarios_percentile(self, percentile_scenarios, included_codes=None):
        """ Each submission has an implicit z-score. Average them. """
        # On the fly discard legacy scenarios where num_predictions are too large
        if included_codes:
            owners_prctls = dict(
                [(self._scenario_owner(s), self._scenario_percentile(s)) for s in percentile_scenarios if
                 (self.shash(self._scenario_owner(s)) in included_codes) and self._scenario_percentile(s) < 1])
        else:
            owners_prctls = dict(
                [(self._scenario_owner(s), self._scenario_percentile(s)) for s in percentile_scenarios if
                 self._scenario_percentile(s) < 1])

        prctls = [p for o, p in owners_prctls.items()]
        mean_prctl = Rediz.zmean_percentile(prctls)

        if prctls and included_codes is not None and len(prctls) < len(included_codes) and abs(mean_prctl - 0.5) > 1e-6:
            if True:
                E = math.exp(8.0 * (mean_prctl - 0.5))
                missing_prctl = (E / (E + 1))
                prctls = prctls + [missing_prctl] * (len(included_codes) - len(prctls))
            return Rediz.zmean_percentile(prctls)
        else:
            return mean_prctl

    def _game_payments(self, pool, participant_set, rewarded_scenarios):
        if len(rewarded_scenarios) == 0:
            do_carryover = np.random.rand() < 0.05
            if do_carryover:
                game_payments = Counter(dict((p, -1.0) for p in participant_set))
                carryover = Counter({self._RESERVE: 1.0 * pool / self.num_predictions})
                game_payments.update(carryover)
            else:
                game_payments = Counter()
        else:
            game_payments = Counter(dict((p, -1.0) for p in participant_set))
            winners = [self._scenario_owner(ticket) for ticket in rewarded_scenarios]
            reward = (1.0 * pool / self.num_predictions) / len(winners)  # Could augment this to use kernel or whatever
            payouts = Counter(dict([(w, reward * c) for w, c in Counter(winners).items()]))
            game_payments.update(payouts)

        if abs(sum(game_payments.values())) > 0.1:
            # This can occur if owners gets out of sync with the scenario hash ... which it should not
            # FIXME: Fail gracefully and raise system alert and/or garbage cleanup of owner::samples::delay::name versus samples::delay::name
            print('********************************************')
            print("Leakage in zero sum game", flush=True)
            pprint(game_payments)
            print('********************************************')
            print('Set all payments to zero, for now, but need to fix this...')
            game_payments = Counter(dict((p, 0.0) for p in participant_set))
        return game_payments

    # --------------------------------------------------------------------------
    #            Implementation  (getters)
    # --------------------------------------------------------------------------

    def _get_lagged_implementation(self, name, with_times, with_values, to_float, start=0, end=None, count=1000):
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
            raw_times = res[1]
        elif with_values and not with_times:
            raw_values = res[0]
            raw_times = None
        elif with_times and not with_values:
            raw_times = res[0]
            raw_values = None

        if raw_values and to_float:
            try:
                values = RedizConventions.to_float(raw_values)
            except:
                values = raw_values
        else:
            values = raw_values

        if raw_times and to_float:
            times = RedizConventions.to_float(raw_times)
        else:
            times = raw_times

        if with_values and with_times:
            return list(zip(times, values))
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
                delayed = RedizConventions.to_float(delayed)
            except:
                pass
        return delayed[0] if singular else delayed

    def _size_implementation(self, name, with_report=False, with_private=False):
        """ Aggregate memory usage of name and derived names """
        derived = list(self.derived_names(name).values())
        private_derived = list(self._private_derived_names(name).values())
        mem_pipe = self.client.pipeline()
        if with_private:
            all_names = [name] + derived + private_derived
        else:
            all_names = [name] + derived
        for n in all_names:
            mem_pipe.memory_usage(n)
        exec = mem_pipe.execute()
        report_data = list()
        for derived_name, mem in zip(all_names, exec):
            try:
                memory = float(mem)
                report_data.append((derived_name, memory))
            except:
                pass
        report = dict(report_data)
        total = sum(list(report.values()))
        report.update({"total": total})
        return report if with_report else total

    def _get_prefixed_implementation(self, prefixed_name):
        """ Interpret things like  delayed::15::air-pressure.json cdf::70::air-pressure.json etc """
        assert self.SEP in prefixed_name, "Expecting prefixed name with " + self.SEP
        parts = prefixed_name.split(self.SEP)
        if len(parts) == 2:
            ps = (parts[0] + self.SEP).lower()
            if ps == self.BACKLINKS:
                data = self.get_backlinks(name=parts[-1])
            if ps == self.SUMMARY:
                data = self.get_summary(name=parts[-1])
            elif ps == self.SUBSCRIPTIONS:
                data = self.get_subscriptions(name=parts[-1])
            elif ps == self.SUBSCRIBERS:
                data = self.get_subscribers(name=parts[-1])
            elif ps == self.LAGGED_VALUES:
                data = self.get_lagged_values(name=parts[-1])
            elif ps == self.CDF:
                data = self.get_cdf(name=parts[-1])
            elif ps == self.LAGGED:
                data = self.get_lagged(name=parts[-1])
            elif ps == self.LAGGED_TIMES:
                data = self.get_lagged_times(name=parts[-1])
            elif ps == self.ERRORS:
                data = self.get_errors(write_key=stem(parts[-1]))
            elif ps == self.PERFORMANCE:
                data = self.get_performance(write_key=stem(parts[-1]))
            elif ps == self.HISTORY:
                data = self.get_history(name=parts[-1])
            elif ps == self.BALANCE:
                data = self.get_balance(write_key=stem(parts[-1]))
            elif ps == self.BUDGETS:
                data = self.get_budget(name=parts[-1])
            elif ps == self.TRANSACTIONS:
                data = self.get_transactions(write_key=stem(parts[-1]))
            elif ps == self.LEADERBOARD:
                data = self.get_leaderboard(name=parts[-1])
            else:
                data = None
        elif len(parts) == 3:
            ps = parts[0] + self.SEP
            if ps == self.DELAYED:
                data = self.get_delayed(name=parts[-1], delay=int(parts[1]), to_float=True)
            elif ps in [self._PREDICTIONS, self.PREDICTIONS]:
                data = self.get_predictions(name=parts[-1], delay=int(parts[1]))
            elif ps in [self._SAMPLES, self.SAMPLES]:
                data = self.get_samples(name=parts[-1], delay=int(parts[1]))
            elif ps == self.LINKS:
                data = self.get_links(name=parts[-1], delay=int(parts[1]))
            elif ps == self.TRANSACTIONS:
                data = self.get_transactions(write_key=parts[1], name=parts[2])
            elif ps == self.LEADERBOARD:
                data = self.get_leaderboard(name=parts[2], delay=int(parts[1]))
            else:
                data = None
        else:
            data = None
        return data

    def _get_implementation(self, name: Optional[str] = None, names: Optional[NameList] = None, **nuissance):
        """ Retrieve value(s). No permission required. Write_keys or other extraneous arguments ignored. """
        plural = names is not None
        names = names or [name]
        res = self._pipelined_get(names=names)
        return res if plural else res[0]

    def _pipelined_get(self, names):
        """ Retrieve name values """
        # mget() may be faster but might be more prone to interrupt other processes? Not sure.
        if len(names):
            get_pipe = self.client.pipeline(transaction=True)
            for name in names:
                get_pipe.get(name=name)
            return get_pipe.execute()

    def _get_history_implementation(self, name, min, max, count, populate, drop_expired):
        """ Retrieve history, optionally replacing pointers with actual values  """
        history = self.client.xrevrange(name=self.HISTORY + name, min=min, max=max, count=count)
        if populate:
            has_pointers = any(self._POINTER in record for record in history)
            if has_pointers and populate:
                pointers = dict()
                for k, record in enumerate(history):
                    if self._POINTER in record:
                        pointers[k] = record[self._POINTER]

                values = self.client.mget(pointers)
                expired = list()
                for k, record in enumerate(history):
                    if k in pointers:
                        if values is not None:
                            fields = RedizConventions.to_record(values[k])
                            record.update(fields)
                            expired.append(k)

                if drop_expired:
                    history = [h for j, h in enumerate(history) if not j in expired]
        return history

    def _get_transactions_implementation(self, min, max, count, write_key=None, name=None, delay=None):
        trnsctns = self.transactions_name(write_key=write_key, name=name, delay=delay)
        data = self.client.xrevrange(name=trnsctns, min=min, max=max, count=count)
        # TODO: Return as numbers??
        return data

    def get_names(self):
        return list(self.client.smembers(self._NAMES))

    @staticmethod
    def _flatten(list_of_lists):
        return [item for sublist in list_of_lists for item in sublist]

    def get_horizon_names(self):
        horizons = list()
        for name in self.get_names():
            for delay in self.DELAYS:
                horizons.append(self.horizon_name(name=name, delay=delay))
        return horizons

    def get_active(self, write_key):
        # FIXME: MUST PIPELINE THIS
        keys = self.get_horizon_names()
        names, delays = self.split_horizon_names(keys)
        active = self.is_active(write_key=write_key, names=names, delays=delays)
        return [k for k, a in zip(keys, active) if a]

    def is_active(self, write_key, names, delays):
        assert len(names) == len(delays), "names/delays length mismatch ... maybe use get_active(write_key) instead"
        pipe = self.client.pipeline()
        for name, delay in zip(names, delays):
            pipe.sismember(self._sample_owners_name(name=name, delay=delay), write_key)
        return pipe.execute()

    def _get_leaderboard_implementation_with_repos(self, leaderboard, readable):
        hash_to_url_dict = self.client.hgetall(name=self._REPOS)
        return OrderedDict(
            [(self.animal_from_code(code), (score, hash_to_url_dict.get(code, None))) for code, score in leaderboard]
        ) if readable else dict([(code, (score, hash_to_url_dict.get(code, None))) for code, score in leaderboard])

    def _get_leaderboard_implementation(self, name, delay, count, readable=True, with_repos=False):
        pname = self.leaderboard_name(name=name, delay=delay)
        leaderboard = list(reversed(self.client.zrange(name=pname, start=-count, end=-1, withscores=True)))
        if with_repos:
            return self._get_leaderboard_implementation_with_repos(leaderboard, readable)
        return OrderedDict([(self.animal_from_code(code), score) for code, score in leaderboard]) if readable else dict(
            leaderboard)

    def _delete_custom_leaderboard_implementation(self, sponsor_code, dt, name=None):
        pname = self.custom_leaderboard_name(sponsor=sponsor_code, dt=dt, name=name)
        self.client.delete(pname)

    def _multiply_custom_leaderboard_implementation(self, sponsor_code, dt, name=None, weight=0.9):
        pname = self.custom_leaderboard_name(sponsor=sponsor_code, dt=dt, name=name)
        temporary_key = 'temporary_' + pname + ''.join([random.choice(['a', 'b', 'c']) for _ in range(20)])
        shrink_pipe = self.client.pipeline(transaction=True)
        shrink_pipe.zunionstore(dest=temporary_key, keys={pname: weight})
        shrink_pipe.zunionstore(dest=pname, keys={temporary_key: 1})
        shrink_pipe.expire(name=temporary_key, time=1)
        exec = shrink_pipe.execute()


    def _get_custom_leaderboard_implementation(self, sponsor_code, dt, count, readable=True, name=None,
                                               with_repos=False):
        pname = self.custom_leaderboard_name(sponsor=sponsor_code, dt=dt, name=name)
        leaderboard = list(reversed(self.client.zrange(name=pname, start=-count, end=-1, withscores=True)))
        if with_repos:
            return self._get_leaderboard_implementation_with_repos(leaderboard, readable)
        return OrderedDict([(self.animal_from_code(code), score) for code, score in leaderboard]) if readable else dict(
            leaderboard)

    def _get_links_implementation(self, name, delay=None, delays=None):
        """ Set of outgoing links created by name owner """
        if delay is None and delays is None:
            delays = self.DELAYS
            singular = False
        else:
            singular = delays is None
            delays = delays or [delay]
        links = [self.client.hgetall(self.links_name(name=name, delay=delay)) for delay in delays]
        return links[0] if singular else links

    def _get_backlinks_implementation(self, name):
        """ Set of links pointing to name """
        return self.client.hgetall(self.backlinks_name(name=name))

    def _get_subscribers_implementation(self, name):
        return list(self.client.smembers(self.subscribers_name(name=name)))

    def _get_subscriptions_implementation(self, name):
        return list(self.client.smembers(self.subscriptions_name(name=name)))

    def _get_predictions_implementation(self, name, delay=None, delays=None, obscure=True):
        return self._get_distribution(namer=self._predictions_name, name=name, delay=delay, delays=delays,
                                      obscure=obscure)

    def _get_samples_implementation(self, name, delay=None, delays=None, obscure=True):
        return self._get_distribution(namer=self._samples_name, name=name, delay=delay, delays=delays, obscure=obscure)

    def _get_index_implementation(self):
        ownership = list(self.client.hgetall(self._OWNERSHIP))
        obscured = [(name, self.animal_from_key(key)) for name, key in ownership.items()]
        obscured.sort(key=lambda t: len(t[1]))
        return obscured

    def _get_distribution(self, namer, name, delay=None, delays=None, obscure=True):
        """ Get predictions or samples and obfuscate (hash) the write keys """
        singular = delays is None
        delays = delays or [delay]
        distribution_names = [namer(name=name, delay=delay) for delay in delays]
        pipe = self.client.pipeline()
        for distribution_name in distribution_names:
            pipe.zrange(name=distribution_name, start=0, end=-1, withscores=True)  # TODO: Return ordered
        private_distributions = pipe.execute()
        data = list()
        for distribution in private_distributions:
            if obscure:
                _data = dict([(self._make_scenario_obscure(scenario), v) for (scenario, v) in distribution])
            else:
                _data = dict([(scenario, v) for (scenario, v) in distribution])
            data.append(_data)
        return data[0] if singular else data

    def _get_summary_implementation(self, name):
        " Stream summary "

        def delay_level(name, delay):
            things = [self.leaderboard_name(name=name, delay=delay), self.delayed_name(name=name, delay=delay),
                      self.links_name(name=name, delay=delay)]
            return dict([(thing, get_json_safe(thing=thing, getter=self.get)) for thing in things])

        def top_level(name):
            things = [name, self.lagged_values_name(name), self.lagged_times_name(name),
                      self.leaderboard_name(name=name),
                      self.backlinks_name(name), self.subscribers_name(name),
                      self.subscriptions_name(name), self.history_name(name),
                      self.messages_name(name)]
            return dict([(thing, shorten(self.get(thing))) for thing in things])

        tl = top_level(name)
        for delay in self.DELAYS:
            tl['delay_' + str(delay)] = delay_level(name=name, delay=delay)
        return tl

    def _get_home_implementation(self, write_key):

        def top_level(write_key):
            things = {'code': self.shash(write_key), 'animal': self.animal_from_key(write_key),
                      self.balance_name(write_key=write_key): self.get_balance(write_key=write_key),
                      'distance_to_bankruptcy': self.distance_to_bankruptcy(write_key=write_key),
                      '/active/' + write_key: self.get_active(write_key=write_key),
                      self.performance_name(write_key=write_key): self.get_performance(write_key=write_key),
                      self.confirms_name(write_key=write_key): self.get_confirms(write_key=write_key),
                      self.errors_name(write_key=write_key): self.get_errors(write_key=write_key),
                      self.warnings_name(write_key=write_key): self.get_warnings(write_key=write_key),
                      self.transactions_name(write_key=write_key): self.get_transactions(write_key=write_key)}
            return dict([(thing, shorten(value, num=10)) for thing, value in things.items()])

        return top_level(write_key=write_key)
