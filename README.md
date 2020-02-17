

## REDIZ

Rediz is a Python package that provides for a shared, specialized use of Redis in the context of open, collective live data prediction.

### TLDR:

At www.3za.org the Rediz library is used to create a public read database that anyone can publish to for a
nominal cost. Streams are keyed by names (strings) that are synonymous with URL's at www.3za.org. 
People create data streams by repeatedly calling set() because it is a cost effective way to receive:
 - History
 - Predictions
 - Normalized data
 - Anomaly detection
 - Assessent of the predictive value of the data 
  
 and other insights including the identities of streams that might be causally related. Rediz is especially well suited to community prediction of civic data streams such as 
 transport, water, electricity and so on. 
  
### Publishing live data

Repeatedly publishing data to the same name creates a stream. 

      rdz = Rediz(**config)
      my_secret_key="eae775f3-a33a-4105-ab8f-77336b0a3921"
      while True:
          time.sleep(15)
          value  = measure_somehow()
          prctl  = rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=value)        

The set() command returns a percentile. Rediz can be used to convert any data into uniformly distributed data. 

#### Ownership (write_key)

Prior to calling set() the user should be in possession of a hard to guess write_key. 

     write_key = rdz.random_key()

If name obscurity is desired this style can also work:  

     title = rdz.random_title()
     rdz.set(**title, value=134.5)
     rdz.set(**title, value=137.1)

whereupon Rediz generates a write_key for the user and also a random stream name. The term title connotates a combination of a name and write_key. 

#### Stream name rules

See the RedizConventions.is_plain_name() for naming rules. Names are intended to be web friendly (no URL escaping) and topic friendly (e.g. SNS). This 
leaves us with alphanumeric, hyphens, underscores, colons (discouraged) and at most one period. Lowercase is encouraged. The name extension must suggest the format. Only .json is supported at present. Names cannot
 contain double colons or tildes as these carry a special significance in Rediz.  

#### Value types

Values are stored as binary strings. However the rediz library infers an implied type when set() is called. The four possibilities are

| type    | Example object    |  Example string                    | Predicted? |
| --------|-------------------|------------------------------------|------------|
| scalar  | 7.0               | '7.3'                              | Yes        |
| vector  | [6,5.3,1.0]       | '[4.0, 5.3, 11.1]'                 | No         |
| dict    | {"age":17}        | '{"temp": 17.3, "pressure": 55.4}' | No         |
| any     | "jamba-juice"     | 'something@other'                  | No         |

where "any" is a catch-all. The Rediz getter methods will typically convert from string to obj unless the user desires otherwise. The RedizConventions class
 document how the type implication is made. 
 
### Derivative data

One motivation for publishing data using set() repeatedly is that Rediz will maintain derived streams.

#### Lagged values (scalar, vector)

The set() command overwrites the previous value, but scalar and vector value revisions are available as a list:

| Example                                    | Intepretation                    |
|--------------------------------------------|----------------------------------|
| lagged_values::air-pressure-06820.json     | List of lagged values            |
| lagged_times::air-pressure-06820.json      | List of lagged times             |

This buffer can be accessed directly with a get() but it is recommended that one use the getter:

    lagged = get_lagged('air-pressure-06820.json',count=20)

which converts to float by default. One can also retrieve time stamps

    lagged = get_lagged('air-pressure-06820.json',with_times=True)

which returns tuples (time,value). The most recent data is returned first.    

#### History (dict, any)

A second way to look at recent history may be more convenient or precise in the case of non-scalar data, or in the case of data where keys are
changing, or when a precise sequence number is required. Rediz also provides history in the form of a log file containing timestamp, sequence
number and fields.

| Example                              | Intepretation                                        |
|--------------------------------------|------------------------------------------------------|
| history::air-pressure-06820.json     | Sequenced, timestamped log of key value pairs        |
| history::huge-data.json              | Log with references to previously set data revisions |

If the value passed to set() is a recognized dict and considered "small", then the history stream will store the values that are passed as key/value pairs. 

| Entry-id              |  Fields                          |
|-----------------------|----------------------------------|
| 1518951480106-0       |  temp  17.5  pressure 110.3      |
| 1518951480106-1       |  temp  34.5                      |
| 1518951480107-0       |  temp  34.5  humidity 94         |

The fields need not be exactly the same each time. The history getter:

    history = get_history("air-pressure-06820.json")

has numerous optional parameters that can help marshall data as required.  If the size of the value is large only a
 reference to the value will be stored in the history and a time to live will ensure expiry of the actual data.

| Entry-id              |  Fields                                       |
|-----------------------|-----------------------------------------------|
| 1518951480106-0       | "<pointer>"    lkjsdlfj9879asd7f9a87f.json    |

It is recommended that the history getter is used to retrieve data as this will perform inflation of values and conversion to float by default. Rediz does
its best to cope with large data values but because the treatment of history is different for large data records, and because the primary intent
is prediction, using set() with values that take up a lot of memory and are not prediction targets can be something of an anti-pattern unless
the data is obviously useful for prediction. 

#### Delayed streams  

Closely related but different to lags and history, Rediz also generates quarantined data.

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| delayed::15:air-pressure-06820.json  | Name holding 15 sec delayed data |

Quarantined data is not made available until a fixed number of seconds has expired since set(). In the above example the data is embargoed
 for 15 seconds. It is by this means www.3za.org acts as a trusted third party allowing users to advertise data
 streams that have been independently delayed for some short period of time. Quarantined data is accessed like any other name:

    rdz.get("delayed:15:air-pressure-06820.json")
    
or via the getter
    
    rdz.get_delayed(name="air-pressure-06820.json", delay=15)

### Prediction

The primary motivation for using Rediz is short term community prediction. Although rediz.samplers contains some rudimentary methods, Rediz is not intended to be an
analytics package per se but rather, a way of orchestrating incentive based prediction. As data arrives, rewards for accurate prediction are computed in
an incremental manner. The data stream creator calling set() need take no further action to initiate prediction. 

#### Accounting 

A set() triggers updates to balances to write_keys. Aggregate rewards can be read by those possessing the write_key, which should only be the owner of said key.  

         get_balance(self, write_key )

#### Providing a univariate stream for prediction 

To provide scalar data for others to predict 

    rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=26.2)  
    rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=37.2)
    etc   

Retrieve predictions via:  

    rdz.get_predictions(name='air-pressure-06820.json', delay=15)
    
or directly 'predictions::15::air-pressure-06820.json' 

#### Predicting univariate streams 

In Rediz, predictions are distributional, as distinct from a single number forecast or so-called point estimate. They take the form of a vector of sorted values, each 
one of which can be considered a scenario. Predictions of
 a data stream can be made by anyone. Those predicting supply their own write_key (used to track their rewards). For example: 

    my_scenarios = sorted(list(np.random.randn(1000)))
    rdz.predict(name="airp-06820.json", write_key="my-obscure-key-81763198236891632", values = my_scenarios, delay=15)

 The delay argument indicates the horizon in seconds. Here "my_scenarios" is a list of scalar values - the same type as the target (i.e. float). The list
  should be of standard length given by rdz.NUM_PREDICTIONS. The list of
values provided can be conceptualized in several ways:

- As a collection of samples of a probabilistic model
- As a more careful collection of quasi-Monte Carlo points
- As sigma points (as with Kalman filtering)
- As an atomic approximation to the distribution. 
- As a kernel approximation to the distribution.  

A future version of Rediz may allow for weights to be supplied alongside scenarios. 

#### Vector data is not predicted 

It is possible to provide streams that are not predicted, simply by providing vector data with len>1 

     rdz.set(name='air-pressure-features.json',write_keys=my_secret_key,values=[99.1,1237.1,123.2,25.5])  

In conjunction with link() this is one way to provide relevant data that is not a primary prediction target pe se. 

#### Providing data for joint (multi-dimensional) prediction 

The set() command also accepts a vector quantity. However this will not trigger prediction. Instead, mset() should be called: 

     names  = [ 'airp-06820.json', 'airp-06821.json', 'airp-06821.json' ]
     values = [ 26.2, 33.4, 44.1 ]
     write_keys = [ write_key for _ in names ]
     budgets = [ 100, 100, 100 ]
     rdz.mset(names=names,values=values, budgets=budgets, write_keys=write_keys) 

This initiates prediction of each of the three variables. However it also creates derived (implied) predictions

- Prediction of implied percentiles 
- Prediction of two and three dimensional implied Copulas

These derived markets are assigned names such as 

    'z1~airp-06820.json'
    'z3~airp-06820~airp-06821~airp-06821.json' 
    
as well as ancilliary streams such as 

    delayed:15:z2~airp-06820~airp-06821~airp-06821.json
    
as with any name. As the reader will infer, Rediz takes a novel, multi-stage approach to multivariate prediction that is
inspired by the theory of Copula functions. 


 
#### Predicting implied z-score streams 

An identical call can be used to predict implied z-scores. 

    my_scenarios = list(np.random.randn(1000))
    rdz.predict(name="z1~airp-06820.json", write_key="my-obscure-key-81763198236891632", values = my_scenarios, delay=15)

Implied z-scores are approximately N(0,1) independent random variables. They are computed by looking at the percentiles of submitted scenarios close to the realized outcome. 

#### Predicting implied z-curve streams 

Once again, an almost identical call replacing predict() with zpredict() can be used to convey opinion about the joint behaviour. 

    my_scenarios = list( [ np.random.randn(3) ] for _ in range(1000) ] )
    rdz.predict3d(name="z3~airp-06820~airp-06821~airp-06821.json", write_key="my-obscure-key-81763198236891632", values = my_scenarios, delay=15)

The predict3d() method will do the following: 

- Convert a three dimensional sample to a one dimensional sample. 
- Call predict(name="z3~airp-06820~airp-06821~airp-06821.json") 

The stream "z3~airp-06820~airp-06821~airp-06821.json" is a univariate stream that is roughly normally distributed. It is a matter of preference as to whether
it is best to predict in three dimensions or one. One can alternatively call rdz.predict() directly, providing univariate samples rather than tri-variate. 

The analogous function predict2d() is a convenience for predicting streams such as "z2~airp-06820~airp-06821.json"

#### Benchmark prediction

The owner of the stream is automatically a participant using predictions generated by Rediz. 
The benchmark prediction algorithm is found in rediz.samples. As noted, the owner of the stream is typically looking to pay for accurate
prediction by others over and above this benchmark. 

#### Collectively generated distributions

Contributed predictions are aggregated in two places:

| Example                                  | Interpretation                                              |
|------------------------------------------|-------------------------------------------------------------|
| samples:60:air-pressure-06820.json       | List of delayed predictions made at least one minute prior  |
| predictions:15:air-pressure-06820.json   | Listing of contemporaneous, 15 second ahead predictions     |

These database entries are sets (actually redis sorted sets) aggregating all predictions or samples from the community. The distinction is that the terminology "samples" refers to delayed predictions which are used to clear the market when a set() is performed, and represent past predictions.

#### Rewards

Submitted scenarios are eligible if they have been quarantined for the minimum time period. 

- We find W winners in a neighborhood (ball) of radius h around the revealed ground truth. 
- Entries inside the ball are rewarded P/(N*W)
- Entries outside the ball are rewarded -1/N.

#### Interpreting predictions

Subject to careful statistical interpretation, various types of projections/moments and other characterization of the preditions can be consumed. For example:

| Example                                      | Interpretation                      | Done? |
|----------------------------------------------|-------------------------------------|-------|
| mean::predictions:60:air-pressure-06820.json | Mean 1 minute forecast              | No    |
| mean::samples:600:air-pressure-06820.json    | Mean ex-post 10 min population std  | No    |
| percentiles::predictions:600:air-pressure-06820.json    | Forecast histogram       | No    |


### Links

A link is a suggestion that one live source of data can predict another. Links can only be created from a delayed stream to a contemporaneous stream. For example:

     link( name=my-wattage-prediction-019871938618326, write_key="my-obsucre-87294812739874109872", target=wattage-019871938618326, delay=300 )

suggests that my-wattage-prediction-019871938618326 has explanatory power five minutes ahead for wattage-019871938618326. It is removed with unlink(). 

### Subscription

Each stream in Rediz can be a subscriber, and comes with a private mailbox where the stream owner can hold messages. The mailbox contains the most recent values of other streams (the subscriptions). 
The methods subscribe() and msubscribe() add subscriptions. 

     msubscribe(name="late-to-class.json", write_key="write_key-blah-2134",
                  sources=["air-pressure-06820.json","humidity-06820.json", "dinky-is-late-06820.json"] )
                  
Messages are retrieved:
                  
     messages = get_messages(name="late-to-class.json", write_key="write_key-blah-2134")

Subscription can be viewed as an on-change hook that tells the subscription streams to propagate values set() or mset() to the subscriber's mailbox. In this way the mailbox can serve
as a last value cache for multiple causally related streams. Subscriptions are removed with 

     unsubscribe(name="late-to-class.json", write_key="write_key-blah-2134",source="air-pressure-06820.json")

### Methods / prefix glossary 

A lagging reference. See rediz.client.Rediz and rediz.conventions.RedizConventions 

#### Creation and maintenance of streams

| Publishing    | write_key? |  Cost |  Interpretation                 | Done? |   
|---------------|-----------|-------|----------------------------------|-------|
| set           | Yes       |  1    | Create predicted stream          | Y     |
| mset          | Yes       |  1000 | Create multi-dimensional streams | Y     |
| delete        | Yes       |  0    | Delete and relinquish ownership  | Y     |
| mdelete       | Yes       |  0    | Relinquish many names            | Y     |


#### Accessing streams and derived quantities by name

Getters and equivalent prefixed names

| Reading           | write_key? |  Cost |  Prefixed example                   | Done? |   
|-------------------|-----------|--------|-------------------------------------|-------|
| get               | No       |  0      |  name                               | Y     |
| mget              | No        |  0     |                                      | Y     |
| get_history       | No        |  1    | history::name                         | Y     |
| get_lagged_values | No        |  0    | lagged_values::name                   | Y     |
| get_lagged_times  | No      |  0      | lagged_times::name                   | Y     |
| get_delayed       | No      |  0      | delayed::15::name                     | Y     |
| get_predictions   | No       |  1     | predictions::15::name                 | Y     |
| get_links         | No       |  1     | links::15::name                       | Y     |
| get_backlinks     | No       |  1     | backlinks::name                       | Y     |
| get_subscriptions | No       |  1     | subscriptions::name                   | Y     |
| get_subscribers   | No       |  1     | subscribers::name                     | Y     |

### Universe 

| Reading       |  Interpretation               | Done? |   
|---------------|-------------------------------|-------|
| card          | Count of all streams             | Y     |
| exists        | Count names that exist in a list | Y     |

#### Subscribing

| Subscription  | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| subscribe     | Yes     |  1    | Subscribe a name to a source     | Y     |
| messages      | Yes     |  0    | Dictionary of received messages  | Y     |
| msubscribe    | Yes     |  100  | Subscribe a name to many sources | Y     |
| unsubscribe   | Yes     |  0    | Unsubscribe a name from a source | Y     |
| munsubscribe  | Yes     |  0    | Unsubscribe a name from sources  | Y     |

#### Links 

| Prediction    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| link          | Yes     |  1    | Suggest a (causal) link          | Y     |                     
| mlink         | Yes     |  100  | Suggest many (causal) links      | Y     |      
| unlink        | Yes     |  0    | Delete a causal link             | Y     |

### Providing predictions 
               
| Prediction    |  Cost |  Interpretation                      | Done? |   
|---------------|-------|--------------------------------------|-------|      
| predict       | 1     | Provide future scenarios             | Y     |                      
| mpredict      |       | Provide 2 or 3 dimensional scenarios | N     |

#### Accounting

| Accounting    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| get_balance   | Yes     |  0    | Net credits for write_key        | Y     |

### Administration

Quarantine is performed by admin_promises, which should be called at least once per second. 

| Method                   | Frequency   |  Interpretation                  |    
|--------------------------|-------------|----------------------------------|
| admin_promises           | < 1 second  | Execute promises                 |
| admin_garbage_collection | < 1 min     | Delete relics of expired names   |

The deletion of disused write_key's is performed by admin_garbage_collection(). Failure to regularly set() a stream's value
will lead eventually to deletion of the stream and all derivative streams, and subsequently to deletion of write_key records. 
Thereupon the name may be recycled by someone else.  
 
#### Rediz/rediz Configuration

Rediz passes through the following constructor arguments to the redis client constructor: 

| Parameter        | Default value | Interpretation    |
|------------------|---------------|-------------------|
| host             |               | URI               |
| port             |               |                   |
| password         |               |                   |

Rediz can also be instantiated with no host, in which case fakeredis will be used. 




### Implementation

#### Obscure system keys

Here "OBSCURE" is some random character sequence

| Redis key                       | Private | Type | Description                                       |
|---------------------------------|---------|------|---------------------------------------------------|
| OBSCURE::ownership              | Yes     | Hash | Official map from name to write_key               |
| OBSCURE::names                  | Yes     | Set  | Redundant set of all names (needed for random sampling when collecting garbage) |
| OBSCURE::promises::1581015806   | Yes     | Set  | List of promises to be executed at 1581015806     |
| OBSCURE::balances               | Yes     | Hash | Tracks cumulative rewards for each write_key      |
| OBSCURE::predictions::900::air-quality.json  | Yes | Sorted set | Predictions with write_keys     |
| OBSCURE::samples::900::air-quality.json  | Yes | Sorted set | Quarantined predictions with write_keys     |
| owners::OBSCURE::samples::900::air-quality.json  | Yes | Sorted set | Redundant list of owners (write_keys) for quarantined predictions  |

#### Transient key usage:

Commands set() and predict() create transient data: 
 
| Example name                          | Type       | Description                                        |
|---------------------------------------|------------|----------------------------------------------------|
| promised::dd92fe65::fake-feed-7fb7    | Value      | Copy made when value is set()                      |
| promised::ddasfff6::fake-feed-7fb7    | Sorted Set | Set of predictions made when predict() called      |

#### Other conventions

Promises take values looking like SOURCE::method::DESTINATION

| Example                                                                                   | Usage      |
|-------------------------------------------------------------------------------------------|------------|
| promised::dc329389::fake-feed-7fb7::predict:OBSCURE::samples::1::fake-feed-7fb76d7c.json' | Samples    |
| promised::d36afe4e::fake-feed-7fb7::copy::delayed::1::fake-feed-7fb76d7c.json'            | Delays     |



### General discussion

We refer the reader to www.3za.org for more information about the motivation for Rediz.

#### Related theory

The reward scheme includes as special cases some well known mechanisms - notably the parimutuel in the case of
 categorical data, although categorical data is not the intended usage. Another useful point of comparison
  is so-called implicit maximum Likelihood estimation. Some theoretical observations:
- A log-wealth maximizing investor constrained to invest all wealth has incentive to contribute paths that reflect her unbiased assessment of the joint distribution, irrespective of paths supplied by others.
- In the case where a contributor adjusts model parameters and then supplies samples from that model, it can be shown that minimizing expected squared distance to the nearest point is equivalent to Maximum Likelihood estimation of the model parameters.

See https://arxiv.org/abs/1809.09087 for a proof of the second statement and http://finmathblog.blogspot.com/2013/11/keeping-punters-log-happy-some.html for the first. 

#### Volumetrics 

Using rediz.NUM_PREDICTIONS=1000, Rediz has been tested at a rate of approximately 100,000 scenario submissions per second. 
This is comparable to the number of orders processed by Nasdaq. 

#### Comparison to ...

To our knowledge Rediz differs markedly from existing software in the broad category of statistical aggregation with economic incentives. This
 category includes such things as prediction markets, exchanges, combinatorial auctions, data science contests and crowdsourcing. Some notable aspects of Rediz:

- There are no point estimates. 
- The online reward mechanism is constant (i.e. O(1)) in the number of participants.    
- Joint probabilities, including 2-Copulas and 3-Copulas, are parametrized by space filling curves. 
- Interrelated marginal, implied zscore and Copula crowd-sourcing encourages separation of concerns.   

#### Possible future improvements

Performance:
- Some consolidation of multiple calls
- Moving more of the logic from Python into Lua scripts.
- Implement 64 bit z-curves 

Features:
- Support for weighted scenarios. 
- Cryptographic verification of delays.
- Exposing some time series functionality
- Data preparation methods for commonly used plotting / blotting packages.
- Darwinian state management (killing useless write_keys et cetera)
- A fifth data type representing a JSON document. 
- More mechanisms driven by links and subscriptions.
- Integration with AutoML and other participant conveniences. 

 
