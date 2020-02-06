


## REDIZ

Rediz is a Python package that provides for a shared, specialized use of Redis in the context of open, collective live data prediction.

### TLDR:

At www.3za.org the Rediz library is used to create a public read, write permission-based shared remote database that anyone can publish data streams to for a nominal cost of their choosing (as little as 0.0001 USD per update). An update overwrites a value in this database keyed by a name (a string, synonymous with a URL at www.3za.org). People publish streams because it is a very cost effective way to receive predictions and insight (such as suggestions for causally related data) and in some cases advances civic and scientific goals. Stream ownership take the form of a write_key (usually a UUID). Every stream update, which is to say a set() or mset(), triggers an extremely lightweight reward mechanism which distributes credits to those making accurate probabilistic micro-forecasts. Rediz is not designed to replace prediction markets aimed at human participation but rather, real-time out of sample Machine Learning and statistical battles between algorithms that might be deployed as running processes or microservices.  

### Publishing live data

The use pattern for consumers of "microprediction" involves repeatedly publishing data to the same name:

      rdz = Rediz(**config)
      my_secret_key="eae775f3-a33a-4105-ab8f-77336b0a3921"
      while True:
          time.sleep(15)
          value = measure_somehow()
          assert rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=value)        

#### Ownership (write_key)

Prior to calling set() the user should be in possession of a hard to guess write_key. For instance:  

     write_key = str(uuid.uuid4())
     write_key = rdz.random_key()

Calling set() the first time claims the name. The example will fail, naturally, if the name 'air-pressure-06820.json' was already taken. It is also possible to use the following style:  

     title = rdz.new(value=123.5)
     rdz.set(**title, value=134.5)
     rdz.set(**title, value=134.5)

whereupon Rediz generates a write_key for the user and, if not supplied, also a random name.

#### Naming rules

RedizConventions documents naming rules. Names are restricted so they can be synonymous with URLs without the need for escaping (and in the future, so they can be synonymous with AWS SNS message topics). Names cannot contain double colons as these carry a special significance in Rediz discussed below.  

#### Value types

In redis values are stored as binary strings. However the rediz library infers an implied type when set() is called. The four possibilities are

| type    | Example object    |  Example string                    |
| --------|-------------------|------------------------------------|
| scalar  | 7.0               | '7.3'                              |
| vector  | [6,5.3,1.0]       | '[4.0, 5.3, 11.1]'                 |
| dict    | {"age":17}        | '{"temp": 17.3, "pressure": 55.4}' |
| any     | "jamba-juice"     | 'something@other'                  |

where any is a catch-all for values that might be .jpeg images, strings or anything acceptable as a Redis value. The Rediz getter methods will typically convert from string to obj unless the user desires otherwise. The RedizConventions class document how the type implication is made.

Future versions of Rediz may support a fifth type representing a JSON document - but this introduces a dependency on Rediz JSON package so has thus far been resisted.

### Derivative data

One motivation for publishing data is that Rediz will maintain derived streams.

#### Lagged values

The set() command overwrites the previous value, but revisions are available as a list:

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| lagged::air-pressure-06820.json     | List of lagged values |

This buffer can be accessed directly with a get() but it is recommended that one use the getter:

    lagged = get_lagged('air-pressure-06820.json',count=20)

which converts to float by default. One can also retrieve time stamps

    lagged = get_lagged('air-pressure-06820.json',with_times=True)

which returns tuples (time,value). The most recent data is returned first.    

#### History

A second way to look at recent history may be more convenient or precise in the case of non-scalar data, or in the case of data where keys are changing, or when a precise sequence number is required. In addition to lagged:: data Rediz also provides history in the form of a Redis style log file containing timestamp, sequence number and fields.

| Example                              | Intepretation                                        |
|--------------------------------------|------------------------------------------------------|
| history::air-pressure-06820.json     | Sequenced, timestamped log of key value pairs        |
| history::huge-data.json              | Log with references to previously set data revisions |

If the value passed to set() is a recognized scalar, vector or dict then the history stream will store the values that are passed as key/value pairs. For "small" dict data, records in a history log might look like the following:

| Entry-id              |  Fields                          |
|-----------------------|----------------------------------|
| 1518951480106-0       |  temp  17.5  pressure 110.3      |
| 1518951480106-1       |  temp  34.5                      |
| 1518951480107-0       |  temp  34.5  humidity 94         |

and we observe that the fields need not be exactly the same each time. On the other hand three dimensional
vector data would appear in the history stream as follows:

| Entry-id              |  Fields                          |
|-----------------------|----------------------------------|
| 1518951480106-0       |  0     17.5  1 54.1  2 123.4     |
| 1518951480106-1       |  0     17.8  1 55.1  2 122.4     |
| 1518951480106-2       |  0     21.1  1 56.1  2 144.4     |

The history getter:

    history = get_history("air-pressure-06820.json")

has numerous optional parameters that can help marshall data as required.  

If the size of the value is large only a reference to the value will be stored in the history and a time to live will ensure expiry of the actual data.

| Entry-id              |  Fields                                       |
|-----------------------|-----------------------------------------------|
| 1518951480106-0       | "<pointer>"    lkjsdlfj9879asd7f9a87f.json    |

It is recommended that the history getter is used to retrieve data as this will perform inflation of values and conversion to float by default.

Rediz does its best to cope with large data values but because the treatment of history is different for large data records, and because the primary intent is prediction, using set() with values that take up a lot of memory and are not prediction targets can be something of an anti-pattern unless the data is useful for prediction. For arbitrary caching of data you are better off just using Redis directly.

#### Delayed streams  

Closely related but different to lags and history, Rediz also generates quarantined data.

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| delayed::15:air-pressure-06820.json  | Name holding 15 sec delayed data |

Quarantined data is not made available until a fixed number of seconds has expired since set(). In the above example the data is embargoed for 15 seconds, and by this means www.3za.org acts as a third party allowing users to advertise data streams (such as predictions) that have been independently delayed for some short period of time. Delayed data does not require a write_key:

    rdz.get("delayed:15:air-pressure-06820.json")
    rdz.get_delayed(name="air-pressure-06820.json", delay=15)

However as noted, owners can always make their names obscure.

### Prediction

The primary motivation for using Rediz is short term prediction. Rediz is not an analytics package per se but rather, orchestrates incentive based prediction by other packages and humans. As data arrives, rewards for accurate prediction are computed in an incremental manner. This updates balances attached to write_keys.

The user creating a stream through repeated use of set() does not need to take any further action in order that prediction occur. They need only browse the results which will, hopefully, become more accurate over time.  The stream of credits provided by set() or mset() subsidizes an otherwise zero-sum game played between contributors. The default subsidy is 1 unit with set() and 1000 units with mset().

#### Predictable values (scalar only for now)

At present only scalar data is predicted. This means the set() operation should be similar to:

    rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=26.2)  

The scalar data is assumed to be continuous. Soon, Rediz prediction will provide better support for:  

- Low dimensional continuous valued data (e.g. R^3, R^4)
- High dimensional continuous valued data (e.g. R^15, R^50)   
- Dictionary style data
- Categorical data
- Ordinal data
- Two dimensional geospatial data (lat/long in geohash)

Cunning users may already be able to use existing Rediz scalar prediction to effect some of these cases.

#### Providing predictions

Predictions of a data stream can be made by anyone supplying a set of value scenarios and a write_key.

    rdz.predict(name="air-pressure-06820.json", write_key="my-obscure-key-81763198236891632", values = my_scenarios)

where here "my_scenarios" is a list of values of the same type as the target (i.e. float for now). The list should be of standard length given by rdz.NUM_PREDICTIONS.

The list of values provided can be conceptualized as a collection of Monte Carlo paths of some model, or quasi-Monte Carlo points (sigma points) providing an atomic approximation. However as the reward scheme effects a smoothing of sorts, perhaps it is most accurate to think about the values provided as a kind of basis for the distribution function. A future version of Rediz may allow for weights to be supplied.


#### Benchmark prediction

The owner of the stream is automatically a participant using predictions generated by Rediz. The benchmark prediction approaches the empirical distribution. As noted, the owner of the stream is typically looking to pay for accurate prediction by others so it is not important that this benchmark be extremely good, merely that there is one.

#### Collectively generated distributions

Contributed predictions are aggregated in two places:

| Example                                  | Interpretation                                              |
|------------------------------------------|-------------------------------------------------------------|
| samples:60:air-pressure-06820.json       | List of delayed predictions made at least one minute prior  |
| predictions:15:air-pressure-06820.json   | Listing of contemporaneous, 15 second ahead predictions     |

These database entries are sets (actually redis sorted sets) aggregating all predictions or samples from the community. The distinction is that the terminology "samples" refers to delayed predictions which are used to clear the market when a set() is performed, and represent past predictions.

#### Rewards (present)

Clearing refers to an incremental, instantaneous adjustment of credits that are associated to write_keys. Upon arrival of a new data point with value "y", the samples are examined and a net gain or loss is assigned to all write_keys associated with all linked delays. These quantities sum to zero, though typically the net gain to the owner of the stream will be negative allowing other linked streams to gain credits on average. If N=1000 say is the number of samples provided by each participant and there are P participants then:

- Samples z in a neighborhood (ball) of y radius h are selected, with h increased if necessary so there is at least one winner. There are W winners.
- Entries inside the ball are rewarded P/(N*W)
- For entries outside the ball, a reward of -1/N is assigned.

Rewards sum to zero.

#### Rewards (proposed)

As noted it may be possible to provide weighted samples soon.

- Weighted samples (w,z) in a neighborhood (ball) of y radius h are selected, with h increased if necessary to include approximately M samples.   
- For entries in the ball, positive rewards R(w,z) proportional to w and a kernel K(x,y) are computed.
- For entries outside the ball, zero reward is assigned.
- All rewards are translated so that they sum to zero.

Clearing rewards sample contributors who provide samples in previously under-sampled regions in the distribution - which might be a joint distribution in the case of vector data.

#### Interpreting predictions

Subject to careful statistical interpretation, various types of projections/moments and other characterization of the preditions can be consumed. For example:

| Example                                      | Interpretation                      | Done? |
|----------------------------------------------|-------------------------------------|-------|
| mean::predictions:60:air-pressure-06820.json | Mean 1 minute forecast              | No    |
| mean::samples:600:air-pressure-06820.json    | Mean ex-post 10 min population std  | No    |
| percentiles::predictions:600:air-pressure-06820.json    | Forecast histogram    | No    |


### Links

We have described the essential mechanics of the Rediz prediction aggregation. We now turn to two features, links and subscriptions, which are less crucial but, hopefully, convenient.

A link is a suggestion that one live source of data can predict another. Links can only be created from a delayed stream to a contemporaneous stream. For example:

     link( prediction=delayed::300::my-wattage-prediction-019871938618326 , target=wattage-019871938618326 )

suggests that my-wattage-prediction-019871938618326 contains samples of the five minute ahead scenarios for actual measured wattage. The link can only be created or removed by the owner of my-wattage-prediction-019871938618326 whose rights extend to the derived stream delayed::300::my-wattage-prediction-019871938618326.

### Subscription

If streams are viewed as nodes on a graph and links one type of edge (running from covariate to a variable that is predicted) then subscriptions can be viewed as edges of a different kind, also suggestive of causality but initiated from the other end. 

A subscription from source to target serves as an instruction to Rediz to propagate changes in the source (i.e. when set(name=source) is called) to a message mailbox attached to the target. The mailbox acts as a last value cache for a plurality of data streams that are, one might presume, of relevance to the prediction of the target stream.

A subscription from source to target does not alter the value stored at target. Source values are propagated only to a special hash (dictionary) called messages::target where they stop.


     msubscribe(name="late-to-class.json", write_key="write_key-blah-2134",
                     sources=["air-pressure-06820.json","humidity-06820.json", "dinky-is-late-06820.json"] )

     messages = get_messages(name="late-to-class.json", write_key="write_key-blah-2134")

There is no information in the mailbox that is not present in the source, and the subscriber could alternatively use mget() on the fly. However subscription can be seen as an optimization that avoids web latency and race conditions. Future improvements to Rediz will likely make other use of subscription as well - such as allowing subscribers to use custom lua scripts for feature generation, propagation to values and so forth.


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

Rediz passes through all relevant constructor arguments to the redis instance initialization.

| Parameter        | Default value | Interpretation    |
|------------------|---------------|-------------------|
| host             |               | URI sans the port |
| port             |               |                   |
| password         |               |                   |

Rediz can also be instantiated with no host, in which case fakeredis will be used. At present Rediz insists on one Redis choice:

| Parameter        | Default value | Interpretation    |
|------------------|---------------|-------------------|
| decode_responses | True          | Can't be modified |


### Implementation

Not obscure:

| Redis key                       | Private | Type | Description                                       |
|---------------------------------|---------|------|---------------------------------------------------|
| predictions::900::air-quality.json  | No | Sorted set | Predictions with obfuscated write_keys     |
| samples::900::air-quality.json  | No | Sorted set | Quarantined predictions obfuscated write_keys     |
| delayed::60::air-quality.json | No | Varies | Quarantined data feed                                 |
| lagged::air-quality.json | No | List | Lagged data feed                                 |
| history::air-quality.json | No | Stream | Timestamped, sequenced  data feed                                 |
| links::60::air-quality.json | No | Set | Outgoing links with lag of 60 seconds                           |
| backlinks::moisture-13244.json | No | Set | Incoming links                                      |
| subscriptions::60::air-quality.json | No | Set | Outgoing links with lag of 60 seconds                           |
| backlinks::moisture-13244.json | No | Set | Incoming links                                      |


Private and obscure:   OBSCURE=some random key

| Redis key                       | Private | Type | Description                                       |
|---------------------------------|---------|------|---------------------------------------------------|
| OBSCURE::ownership              | Yes     | Hash | Official map from name to write_key               |
| OBSCURE::names                  | Yes     | Set  | Redundant set of all names (needed for random sampling when collecting garbage) |
| OBSCURE::promises::1581015806   | Yes     | Set  | List of promises to be executed at 1581015806     |
| OBSCURE::balances               | Yes     | Hash | Tracks cumulative rewards for each write_key      |
| OBSCURE::predictions::900::air-quality.json  | Yes | Sorted set | Predictions with write_keys     |
| OBSCURE::samples::900::air-quality.json  | Yes | Sorted set | Quarantined predictions with write_keys     |
| owners::OBSCURE::samples::900::air-quality.json  | Yes | Sorted set | Redundant list of owners (write_keys) for quarantined predictions  |

Transient key usage:

| Redis key                                 | Type  | Description                                        |
|-------------------------------------------|-------|----------------------------------------------------|
| promised::dd92fe65::fake-feed-7fb7        | Value | Copy made when value is set()                      |
| promised::ddasfff6::fake-feed-7fb7        | Sorted Set | Set of predictions made when predict() called |

Promise format is  SOURCE::method::DESTINATION

| Example                                                                                  | Usage      |
|------------------------------------------------------------------------------------------|------------|
| promised::dc329389::fake-feed-7fb7::ticket:OBSCURE::samples::1::fake-feed-7fb76d7c.json' | Samples    |
| promised::d36afe4e::fake-feed-7fb7::copy::delayed::1::fake-feed-7fb76d7c.json'           | Delays     |









### General discussion

We refer the reader to www.3za.org for more information about the motivation for Rediz.

#### Theory

Through judicious choice of parameters this reward scheme includes as special cases some well known mechanisms - notably the parimutuel in the case of categorical data though that is not the intended focus. Another useful point of comparison is so-called implicit maximum Likelihood estimation. Some theoretical observations informing the reward mechanism include the following:
- A log-wealth maximizing investor constrained to invest all wealth has incentive to contribute paths that reflect her unbiased assessment of the joint distribution, irrespective of paths supplied by others.
- In the case where a contributor adjusts model parameters and then supplies samples from that model, it can be shown that minimizing expected squared distance to the nearest point is equivalent to Maximum Likelihood estimation of the model parameters.

See https://arxiv.org/abs/1809.09087 for a proof of the second statement and http://finmathblog.blogspot.com/2013/11/keeping-punters-log-happy-some.html for the first. However when players are allowed to form coalitions, a possible future feature, the interpretation is more complex.

#### Comparison to prediction markets and related packages

To our knowledge Rediz differs from existing software in the broad category of statistical aggregation with economic incentives. This
 category includes such things as prediction markets, exchanges, data science contests and crowdsourcing. The approach taken herein differs
 in engineering aspects as well as focus (streaming public data).

- Clearing operations are O(1)  
- There is no temporal state (e.g. limit orders, wagers), only guaranteed data delays and samples.
- Settlement is instantaneous.
- Every quantity has a distributional estimate.

The last statement refers back to the fact that every data stream predicts itself - albeit somewhat poorly as a Dirac distribution centered on the last value. Maintainers of streams can use mset() rather than set() to increase the subsidy beyond one credit.    

#### Improvements

Performance
- Consolidation of multiple calls
- Moving more of the logic from Python into Lua scripts.

Features
- Cryptographic verification of delays.
- Exposing some time series functionality
- Data preparation methods for commonly used plotting packages.
- Pushing to commonly used blotter/tabular visualization packages.
