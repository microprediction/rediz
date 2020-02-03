


## REDIZ

Rediz is a Python package that provides for a shared, specialized use of Redis in the context of open, collective live data prediction.

At www.3za.org Rediz is used to create a public read, write permission-based shared remote database that anyone can publish data streams to for a nominal cost of their choosing (as little as 0.0001 USD per update). An update overwrites a value in this database keyed by a name (string). At www.3za.org the name is synonymous with a URL. Stream ownership take the form of a write_key which is ideally set by the user and typically a UUID. Every stream update, which is to say a set() or mset(), triggers the clearing of a so-called "nano-market": an extremely lightweight reward mechanism which distributes credits to owners of other data streams according to how accurately delayed versions of their data forecast the newly arriving data point.

### Publishing live data

The use pattern involves repeatedly publishing data to the same name:

      rdz = Rediz(**config)
      my_secret_key="eae775f3-a33a-4105-ab8f-77336b0a3921"
      while True:
          time.sleep(15)
          value = json.dumps(measure_somehow())
          assert rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=value)        

This will fail if the name 'air-pressure-06820.json' was already taken. Downstream, other capabilities may fail quietly if a publishing pattern is difficult for Rediz to interpret - such as if the implicit schema changes from one set() to the next. Users are encouraged to err on the side of simplicity and publish easy to guess data streams such as single scalar values, vectors of consistent length or dictionaries with mostly consistent keys.

#### Value types  

While any binary string can be set(), the valuable prediction capability of Rediz supports:

- One dimensional continuous valued data (as float or int)
- Two dimensional geospatial data (lat/long in geohash)
- Low dimensional continuous valued data (e.g. R^3, R^4)
- High dimensional continuous valued data (e.g. R^200)   

Furthermore users can readily adapt this to:

- Categorical data (float, with some interpretation)
- Ordinal data (using float, with appropriate monotone transformations as required)

### Derivative data

One motivation for publishing data is that Rediz will maintain derived streams.

#### History

A prefixed stream is created:

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| history::air-pressure-06820.json     | Log with links to data revisions |

History is a timestamped record of changes. Once a value is set() it is replicated to
an immutable value with an obscure name referenced in the history log. The data will expire
and should be preserved by some other means if that is desirable.

#### Delayed streams  

Rediz also creates derivative streams such as:

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| delayed::15:air-pressure-06820.json  | Name holding 15 sec delayed data |

An instance of Rediz can thereby act as a trusted third party allowing users to advertise data streams (such as predictions) that have been independently verified as quarantined for some short period of time.

    rdz.get("air-pressure-06820.json")
    rdz.get("delayed:15:air-pressure-06820.json")

No permissions are required to read, though owners can always make their names obscure.

### Prediction

The real motivation for using Rediz is short term prediction. Rediz is not an analytics package per se but rather, orchestrates incentive based prediction by other packages and humans. Prediction is achieved in an incremental manner designed to minimize all kinds of friction - both technological and economic - and hopefully achieving a good accuracy to cost ratio in the process. The budget, as noted, is set by the stream creator.

#### Links

A link is a suggestion, taken rather seriously, that one live source of data is an approximation of another and is prepared to be judged on the merits. Links can only be created from a delayed stream to a contemporaneous stream. For example:

     link( prediction=delayed::300::my-wattage-prediction-019871938618326 , target=wattage-019871938618326 )

suggests that my-wattage-prediction-019871938618326 contains samples of the five minute ahead scenarios for actual measured wattage. The link can only be created or removed by the owner of my-wattage-prediction-019871938618326 whose rights extend to the derived stream delayed::300::my-wattage-prediction-019871938618326.

#### Samples  

The stream of credits provided by set() and mset() subsidizes an otherwise zero-sum game
played between contributors of "samples" of the future (think scenarios, Monte Carlo paths or atomic approximations of distributions implicitly smoothed by the reward scheme). Every stream has an associate prediction term structure retrieved
using time indexed names such as:

| Example                                  | Interpretation                                              |
|------------------------------------------|-------------------------------------------------------------|
| samples:60:air-pressure-06820.json       | List of delayed predictions made at least one minute prior  |
| predictions:15:air-pressure-06820.json   | Listing of contemporaneous, 15 second ahead predictions     |

These database entries are sets (actually redis sorted sets) aggregating all predictions or samples from the community. The not so subtle and important distinction is that samples are used to clear the market when a set() is performed, and represent past predictions. In contrast predictions are a collection of recently set values which will subsequently appear in a delay:: stream.

For predictions to appear they must be linked. Linking is the mechanism whereby users nominate a stream as an probabilistic approximation of another (that is to say, they nominate a stream holding a vector of paths and a target stream which is a single quantity). Links can only be made from system generated delay:: streams to contemporaneous streams (those with no delays).


#### Clearing

Clearing refers to an incremental, instantaneous adjustment of credits that are associated to write_keys. Upon arrival of a new data point with value "y", the samples are examined and a net gain or loss is assigned to all write_keys associated with all linked delays. These quantities sum to zero, though typically the net gain to the owner of the stream will be negative allowing other linked streams to gain credits on average.

One way to understand clearing is via an idealized mechanism:  

- Weighted samples (w,z) in a neighborhood (ball) of y radius h are selected, with h increased if necessary to include approximately M samples.   
- For entries in the ball, positive rewards R(w,z) proportional to w and a kernel K(x,y) are computed.
- For entries outside the ball, zero reward is assigned.
- All rewards are translated so that they sum to zero.

Clearing rewards sample contributors who provide samples in previously under-sampled regions in the distribution - which might be a joint distribution in the case of vector data.

In fact clearing does not proceed exactly as described, except when data is one dimensional. Rediz' obsession with O(1) clearing mandates some modifications whose justification is more lengthy.

#### Theory

Through judicious choice of parameters this reward scheme includes as special cases some well known mechanisms - notably the parimutuel in the case of categorical data though that is not the intended focus. Another useful point of comparison is so-called implicit maximum Likelihood estimation. Some theoretical observations informing the reward mechanism include the following:
- A log-wealth maximizing investor constrained to invest all wealth in a parimutuel has incentive to contribute paths that reflect her unbiased assessment of the joint distribution.
- In the case where a contributor adjusts model parameters and then supplies samples from that model, it can be shown that minimizing expected squared distance to the nearest point is equivalent to Maximum Likelihood estimation of the model parameters.

See https://arxiv.org/abs/1809.09087 for a proof of the second statement and http://finmathblog.blogspot.com/2013/11/keeping-punters-log-happy-some.html for the first. However when players are allowed to form coalitions, a possible future feature, the interpretation is more complex.

#### Summary statistics

Subject to careful statistical interpretation, various types of projections/moments and other characterization of the nanomarket is available. For example:

| Example                                      | Interpretation                      | Done? |
|----------------------------------------------|-------------------------------------|-------|
| mean::predictions:60:air-pressure-06820.json | Mean 1 minute forecast              | No    |
| mean::samples:600:air-pressure-06820.json    | Mean ex-post 10 min population std  | No    |
| hist::samples:600:air-pressure-06820.json    | Mean ex-post 10 minute histogram    | No    |

Every stream has at least one distributional estimate: the Dirac sample provided by set() or mset(). This default participant seeds the market in a trivial fashion: providing only one sample equal to the current value. So these quantities are always returned but may not be terribly accurate for young streams.

### Subscription

Clearing, which relies on links, provides the economic incentive for participation. Subscription is a "mere" convenience for participants.

If streams are viewed as nodes on a graph and links one type of edge (running from delayed predictor to target and initiated by the former), then subscriptions can be viewed as edges running in the opposite direction (from contemporaneous streams typically to subscribers) and initiated by subscriber rather than the other way around.

In Rediz, a subscription is really an invitation for future set() commands to propagate "on-change messages" which populate a key/value store set aside for one particular name (the subscriber). This is a means of tracking the value changes of one or more streams that are relevant to production of the subscribing stream (presumably - though that is up to the owner). Note that subscription does not alter the value stored at the subscribing stream per se - so it is not by default a means of propagating values through the network. Instead, values are propagated only to messages::<name> (a mailbox) where they stop. Messages can be accessed on demand by the owner (using the write_key) to reveal a dictionary. The keys in this dictionary are the names of the tracked streams and the values are their current values.

There is no information in the mailbox that is not present in the tracked streams. Because the subscriber could alternatively gather all values from said pages with an mget(), subscription can be seen purely as an optimization (assuming this is the case, which for rapidly changing tracked pages might not be). However subscription avoids latency and race conditions, simplifies the tracking of hints as to what is useful to whom, and, together with other conventions for the way in which external models can be invoked, warrants inclusion as a core mechanism. Alos, future improvements to Rediz will likely make other use of subscription as well, such as immediate propagation via lua scripts, non-trivial lag generation and so forth.

#### Feature spaces

Evidently feature spaces can be created and maintained by subscription. The msubscribe() call makes this more convenient:

     msubscribe(name="my-model-12341.json", write_key="write_key-blah-2134",
                     sources=["air-pressure-06820.json","humidity-06820.json", "dinky-is-late-06820.json"] )

#### Lags and buffering

Another pattern of subscription involves subscribing to multiple delays of the same stream. For example:

     subscribe("my-model-12341.json", "write_key-blah-2134", "air-pressure-06820.json")
     subscribe("my-model-12341.json", "delayed::5::write_key-blah-2134", "air-pressure-06820.json")
     subscribe("my-model-12341.json", "delayed::10::write_key-blah-2134", "air-pressure-06820.json")

will ensure population of a cache that acts as a recent values buffer for the model - which might be a moving average model for example. There is a shorthand for this common use:

    subscribe(name="my-model-12341.json", write_key="write_key-blah-2134", source="air-pressure-06820.json", delays=[0,5,10])

Rediz is Pythonic and there is no right way. One can also use the history:: functionality to build combinations of lagged and contemporaneous values.


### Listing of all public methods

Keys column indicates whether permission in the form of a write_key is required. Suggested cost
is in credits where 1 credit=0.0001 USD.

#### Creation and maintenance of streams

| Publishing    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| set           | Yes     |  1    | Create/modify value at one name  | Y     |
| mset          | Yes     |  1000 | Create/modify many name/values   | Y     |
| setlog        | Yes     |  0    | Retrieve set execution log/errors| N     |
| new           | No      |  1    | Create a name w/o providing key  | Y     |
| mnew          | No      |  1000 | Create many names w/o keys       | Y     |
| delete        | Yes     |  0    | Delete and relinquish ownership  | Y     |
| mdelete       | Yes     |  0    | Relinquish many names            | Y     |


#### Accessing streams

| Reading       | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| get           | No      |  0    | Retrieve a value (one name)      | Y     |
| mget          | No      |  0    | Retrieve from many names         | Y     |
| history       | No      |  0    | Shorthand for get("history::.."")| N     |
| delayed       | No      |  0    | Shorthand for get("delayed::.."")| N     |
| card          | No      |  0    | Count of all names               | Y     |
| exists        | No      |  0    | Count names that exist in a list | Y     |
| proof         | No      |  1    | Provide cryptographic delay proof| N     |

#### Subscribing

| Subscription  | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| subscribe     | Yes     |  1    | Subscribe a name to a source     | Y     |
| messages      | Yes     |  0    | Dictionary of received messages  | Y     |
| msubscribe    | Yes     |  0    | Subscribe a name to many sources | Y     |
| unsubscribe   | Yes     |  0    | Unsubscribe a name from a source | Y     |
| munsubscribe  | Yes     |  0    | Unsubscribe a name from sources  | Y     |
| subscriptions | Yes     |  0    | List of a name's subscriptions   | Y     |
| subscribers   | Yes     |  0    | List of a name's subscriptions   | Y     |

#### Participating in prediction

| Prediction    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| link          | Yes     |  1    | Suggest a (causal) link          | Y     |                     
| mlink         | Yes     |  1000 | Suggest many (causal) links      | Y     |                     
| predict       | Yes     |  1    | Equivalent to set then link      | N     |                      
| mpredict      | Yes     |  1000 | Equivalent to mset + mlink       | N     |
| unlink        | Yes     |  0    | Delete a causal link             | N     |
| links         | Yes     |  0    | List outgoing links              | N     |
| backlinks     | Yes     |  0    | List incoming links              | N     |

#### Consuming prediction

| Population    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| samples       | No      |  0    | List of delayed samples          | N     |
| predictions   | No      |  1    | List of contemporaneous samples  | N     |
| hsamples      | No      |  0    | Histogram of samples             | N     |
| hpredictions  | No      |  0    | Histogram of predictions         | N     |
| mean          | No      |  0    | Pop. mean of samples or preds    | N     |
| std           | No      |  0    | Population std of                | N     |

#### Accounting

| Accounting    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| balance       | Yes     |  0    | Net credits for write_key        | N     |
| performance   | No      |  0    | Net credits for write_key/name(s)| N     |
| hbalance      | Yes     |  0    | Wealth percentiles               | N     |
| hperformance  | No      |  0    | Performance percentiles          | N     |


### Administration

For Rediz to function these methods must be called by the system

| Method                   | Frequency  |  Interpretation                  |    
|--------------------------|------------|----------------------------------|
| admin_garbage_collection | < 15 mins   | Delete relics of expired names  |
| admin_promises           | < 1 second  | Execute promises                |

#### Garbage collection

Rediz exploits Redis data expiry to avoid unfunded growth in the database. When a value is set a time to live is determined that is inversely proportional to the memory consumption. And as far as streams's are concerned, possession is nine-tenths of the law. Failure to regularly set() a stream's value will lead eventually to value expiry and subsequently to relinquishing of ownership of the name.

The deletion of disused write_key's is performed by admin_garbage_collection(), which should be run periodically. This system process also deletes other relics of the disused data stream such as delays and messages. Garbage collection performs a stochastic sampling of ownership (write_key) to check whether the data
has expired. Only a small fraction of all streams are checked to avoid slowing down Redis, so this should be run frequently.

#### Promises

Internally, promises are lists of copy operations from streams to delays of the same stream. They are grouped by second or sub-second epoch times. A daemon executes pending operations and should be run at least every second.

#### Rediz/rediz Configuration

Rediz passes through all constructor arguments to the redis instance initialization. It has
been tested with the following means of initializing a redis client.

| Parameter        | Default value | Interpretation    |
|------------------|---------------|-------------------|
| decode_responses | True          | Can't be modified |
| host             |               | URI sans the port |
| port             |               |                   |
| password         |               |                   |

Rediz can also be instantiated with no host, in which case fakeredis will be used.  



### Comparison to prediction markets and related packages

To our knowledge Rediz differs from existing software in the broad category of statistical aggregation with economic incentives. This
 category includes such things as prediction markets, exchanges, data science contests and crowdsourcing. The approach taken herein differs
 in engineering aspects as well as focus (streaming public data).

- Clearing operations are O(1)  
- There is no temporal state (e.g. limit orders, wagers), only guaranteed data delays and samples.
- Settlement is instantaneous.
- Every quantity has a distributional estimate.

The last statement refers back to the fact that every data stream predicts itself - albeit somewhat poorly as a Dirac distribution centered on the last value. Maintainers of streams can use mset() rather than set() to increase the subsidy beyond one credit.    

### Intended future improvements

Performance
- Consolidation of multiple calls
- Moving more of the logic from Python into Lua scripts.

Features
- Cryptographic verification of delays.
- Exposing some time series functionality
- Data preparation methods for commonly used plotting packages.
- Pushing to commonly used blotter/tabular visualization packages.
