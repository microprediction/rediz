
# Server side notes (rediz library)
  
At www.microprediction.org client requests using the microprediction library are (mostly) handled by the rediz library. 
  
## Publishing live data

Repeatedly publishing scalar data to the same name creates a stream. 

      rdz = Rediz(**config)
      my_secret_key=rdz.create_key(difficulty=12)  # This takes all day :)
      while True:
          time.sleep(15)
          value  = measure_somehow()
          res  = rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=value)        

The set() command returns percentiles in the results. Rediz can be used to convert any data into uniformly distributed data. 

#### Stream name rules (rediz)

See https://github.com/microprediction/microconventions/tree/master/microconventions

#### Rediz value types

At present only scalar values such as https://www.microprediction.org/live/cop.json are predicted. It is, however, possible to write non-scalar values should that prove useful. 
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

The set() command overwrites the previous value, but scalar and vector value revisions are available as a list. 

| Example                                    | Intepretation                                            |
|--------------------------------------------|----------------------------------------------------------|
| lagged_values::air-pressure-06820.json     | List of lagged values       |
| lagged_times::air-pressure-06820.json      | List of lagged times             |

This buffer can be accessed directly with a get() but it is recommended that one use the getter:

    lagged = get_lagged('air-pressure-06820.json',count=20)

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

| Entry-id              |  Fields                                                               |
|-----------------------|-----------------------------------------------------------------------|
| 1518951480106-0       |  POINTER_TO_ACTUAL_DATA                lkjsdlfj9879asd7f9a87f.json    |

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
 for 15 seconds. It is by this means www.microprediction.org acts as a trusted third party allowing users to advertise data
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
    
or directly 'predictions::15::air-pressure-06820.json'   At present this is not exposed in the microprediction client. However the client does contain
a get_cdf method

#### Predicting univariate streams 

In Rediz, predictions are distributional, as distinct from a single number forecast or so-called point estimate. They take the form of a vector of sorted values, each 
one of which can be considered a scenario. Predictions of
 a data stream can be made by anyone. Those predicting supply their own write_key (used to track their rewards). For example: 

    my_scenarios = sorted(list(np.random.randn(rdz.NUM_PREDICTIONS)))
    rdz.predict(name="airp-06820.json", write_key="e151e1df704b69a2800d01ccf64f90bc", values = my_scenarios, delay=15)

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

For example: 

     rdz.set(name='air-pressure-features.json',write_keys=my_secret_key,values=[99.1,1237.1,123.2,25.5])  

will not trigger prediction. In conjunction with link() this is one way to provide relevant data that is not a primary prediction target pe se. At time 
of writing the client library microprediction does not support this, only scalar setting. 

#### Providing data for joint (multi-dimensional) prediction 

At www.microprediction.org the copula API provides some advanced functionality. This is implemented in rediz with cset()

     names  = [ 'airp-06820.json', 'airp-06821.json', 'airp-06821.json' ]
     values = [ 26.2, 33.4, 44.1 ]
     write_keys = [ write_key for _ in names ]
     budgets = [ 100, 100, 100 ]
     rdz.cset(names=names,values=values, budgets=budgets, write_keys=write_keys) 

There is also a cset method in the microprediction client

A cset call initiates derived (implied) predictions

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

Because space filling curves are used, there is no API difference between predicting scalar time series and predicting more complex
quantities such as the image of an implied copula on a Morton curve. 

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

Rewards, both positive and negative, are calculated upon arrival of every data point (when cset or set are called). At this
time the predictions zsets are searched. 

- Submitted scenarios are eligible if they have been quarantined for the minimum time period. 
- We find W winners in a neighborhood (ball) of radius h around the revealed ground truth. 
- Entries inside the ball are rewarded P/(N*W)
- Entries outside the ball are rewarded -1/N.

The method of determining the W winners is undergoing change but at time of writing:
 
- We search near the value with a tight window
- We backoff and enlarge the window if no winner is found

### Links

A link is a suggestion that one live source of data can predict another. Links can only be created from a delayed stream to a contemporaneous stream. For example:

     link( name=my-wattage-prediction-019871938618326, write_key="my-obsucre-87294812739874109872", target=wattage-019871938618326, delay=300 )

suggests that my-wattage-prediction-019871938618326 has explanatory power five minutes ahead for wattage-019871938618326. It is removed with unlink(). 

This functionality is not currently exposed in the client library. 

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
| set_scenarios       | 1     | Provide future scenarios             | Y     |                      

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


#### Leaderboards 

A bunch of these are exposed. See rediz.client for various kinds. 

