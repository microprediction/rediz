


## REDIZ

Rediz is a Python package that provides for a shared, specialized use of Redis in the context of open, collective live data prediction.

At www.3za.org Rediz is used to create a public read, write permission-based shared remote database that anyone can publish data streams to for a fairly nominal cost (0.0001 USD per update). An update overwrites a value in this database keyed by a name (a name being almost synonymous with with a URL) and permissioned by a write_key which the owner establishes. Every such update triggers the clearing of a so-called "nano-market": an extremely lightweight reward mechanism which distributes this tiny amount of money to owners of other data streams according to how accurately delayed versions of their data forecast the newly arriving data point.

### Publishing live data

The use pattern involves repeatedly publishing data to the same name:

      rdz = Rediz(**config)
      my_secret_key="eae775f3-a33a-4105-ab8f-77336b0a3921"
      while True:
          time.sleep(15)
          value = json.dumps(measure_somehow())
          assert rdz.set(name='air-pressure-06820.json',write_key=my_secret_key,value=value)        

This will fail if the name 'air-pressure-06820.json' was already taken. Possession is nine tenths of the law. If publication to the steam ceases the ownership rights will eventually be relinquished - data in the form of values will also expire.

### Delayed data

However, assuming continuous use, derivatives of this live data will be maintained such as:

| Example                              | Intepretation                    |
|--------------------------------------|----------------------------------|
| history::air-pressure-06820.json     | Log with links to data revisions |
| delayed::15:air-pressure-06820.json  | Name holding 15 sec delayed data |

In this way Rediz acts as an independent third party allowing users to advertise live data, and also advertise data streams (such as predictions) that have been independently verified as quarantined for some short period of time. Please contact us if you would like to contribute a Merkel hash or other scheme to add strength to this statement. Delayed and live data can be read with get. For example:  

    rdz.get("air-pressure-06820.json")
    rdz.get("delayed:15:air-pressure-06820.json")

No permissions are required to read, though owners can always make their names obscure.

### Links

A link is a suggestion, taken rather seriously, that one live source of data is an approximation of another and is prepared to be judged on the merits. Links can only be created from a delayed stream to a contemporaneous stream. For example:

     link( prediction=delayed::300::my-wattage-prediction-019871938618326 , target=wattage-019871938618326 )

suggests that my-wattage-prediction-019871938618326 contains samples of the five minute ahead scenarios for actual measured wattage. The link can only be created or removed by the owner of my-wattage-prediction-019871938618326 whose rights extend to the derived stream delayed::300::my-wattage-prediction-019871938618326.

Links are similar to subscriptions but there are two important differences. First, the connection is initiated in the opposite direction. Second, the implied propagation is more complex.

### Nanomarkets, scenarios and forecasts (coming soon)

Using the contribute to Monte Carlo scenarios describing possible future values. The prefixes refer to market-like mechanisms used under the hood which provide incentive for contributors to provide
samples which individually or collectively map the joint distribution accurately.

| Example                           | Interpretation                        |
|-----------------------------------|---------------------------------------|
| nano:60:air-pressure-06820.json   | Listing of 1 minute ahead scenarios   |
| near:15:air-pressure-06820.json   | Listing of 15 second ahead scenarios  |

At present the available nanomarkets and choices of prefix are:

| Prefix | Name         | Interpretation and properties                              |
|--------|--------------|------------------------------------------------------------|
| nano   | Nanomutuel   | A relative compensation scheme analogous to a pari-mutuel clearing mechanism but extending to high dimensions. Nano-markets reward contributors who provide samples in previously under-sampled regions in the joint distribution. A log-wealth maximizing investor constrained to invest all wealth has incentive to contribute paths that reflect her unbiased assessment of the joint distribution.  |
| near   | Nearest Squared Error     | Based on high performers in an absolute compensation scheme where the criteria is squared distance between the realized outcome and the nearest scenario. In the case where a contributor adjusts model parameters and then supplies samples from that model, it can be shown that minimizing expected squared distance to the nearest point is equivalent to Maximum Likelihood estimation of the model parameters. See https://arxiv.org/abs/1809.09087 for a proof. When players are allowed to form coalitions the interpretation is more complex.

### Point estimate predictions

Subject to careful statistical interpretation, point estimates can be
directly read at name/values with the following patterns:

| Example                                   | Interpretation              |
|-------------------------------------------|-----------------------------|
| mean::nano:60:air-pressure-06820.json     | Mean 1 minute forecast      |
| mean::near:600:air-pressure-06820.json    | Mean 10 minute forecast     |

It is worth remarking that Dirac samples can also be thought of as point estimates, again with the usual caveats. Nanomarkets begin in this Dirac state: a single contributor automatically provided by delay::SECONDS::NAME. This default participant seeds the market in a trivial fashion: providing only one sample equal to the current value. In the absence of any other contributions this always "wins", but since the delay::SECONDS:NAME and NAME are owned by the same write_key the economics net to zero. In this sense every quantity is predicted.  

### Public methods

Listing of methods, whether permission in the form of a write_key is required, and suggested cost model (1 unit=0.0001 USD)

| Publishing    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| set           | Yes     |  1    | Create/modify value at one name  | Y     |
| mset          | Yes     |  1000 | Create/modify many name/values   | Y     |
| setlog        | Yes     |  0    | Retrieve set execution log/errors| N     |
| new           | No      |  1    | Create a name w/o providing key  | Y     |
| mnew          | No      |  1000 | Create many names w/o keys       | Y     |
| delete        | Yes     |  0    | Delete and relinquish ownership  | Y     |
| mdelete       | Yes     |  0    | Relinquish many names            | Y     |
|---------------|---------|-------|----------------------------------|-------|
| Reading       | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| get           | No      |  0    | Retrieve a value (one name)      | Y     |
| mget          | No      |  0    | Retrieve from many names         | Y     |
| history       | No      |  0    | Shorthand for get("history::.."")| N     |
| delayed       | No      |  0    | Shorthand for get("delayed::.."")| N     |
| card          | No      |  0    | Count of all names               | Y     |
| exists        | No      |  0    | Count names that exist in a list | Y     |
|---------------|---------|-------|----------------------------------|-------|
| Subscription  | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| subscribe     | Yes     |  1    | Subscribe a name to a source     | Y     |
| messages      | Yes     |  0    | Dictionary of received messages  | Y     |
| msubscribe    | Yes     |  0    | Subscribe a name to many sources | Y     |
| unsubscribe   | Yes     |  0    | Unsubscribe a name from a source | Y     |
| munsubscribe  | Yes     |  0    | Unsubscribe a name from sources  | Y     |
| subscriptions | Yes     |  0    | List of a name's subscriptions   | Y     |
| subscribers   | Yes     |  0    | List of a name's subscriptions   | Y     |
|---------------|---------|-------|----------------------------------|-------|
| Prediction    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| link          | Yes     |  1    | Suggest a (causal) link          | Y     |                     
| mlink         | Yes     |  1000 | Suggest many (causal) links      | Y     |                     
| predict       | Yes     |  1    | Equivalent to set then link      | N     |                      
| mpredict      | Yes     |  1000 | Equivalent to mset + mlink       | N     |
| unlink        | Yes     |  0    | Delete a causal link             | N     |
| links         | Yes     |  0    | List outgoing links              | N     |
| backlinks     | Yes     |  0    | List incoming links              | N     |
| samples       | No      |  0    | List of delayed samples          | N     |
| predictions   | No      |  1    | List of contemporaneous samples  | N     |
| hsamples      | No      |  0    | Histogram of samples             | N     |
| hpredictions  | No      |  0    | Histogram of predictions         | N     |
|---------------|---------|-------|----------------------------------|-------|
| Accounting    | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| balance       | Yes     |  0    | Net credits for write_key        | N     |
| performance   | No      |  0    | Net credits for write_key/name(s)| N     |
| hbalance      | Yes     |  0    | Wealth percentiles               | N     |
| hperformance  | No      |  0    | Performance percentiles          | N     |


### Administrative methods

Rediz exploits Redis data expiry to avoid unfunded growth in the database. When a value is set a time to live is determined that is
inversely proportional to the memory consumption. And as far as streams's are concerned, possession is nine-tenths of the law.
Failure to regularly set() a stream's value will lead eventually to value expiry and subsequently to relinquishing of ownership of the name.
The deletion of disused write_key's is performed by admin_garbage_collection(), which should be run periodically. This system process also deletes other relics of the disused data stream such as
delays and messages. Garbage collection performs a stochastic sampling of ownership (write_key) to check whether the data
has expired. Only a small fraction of all streams are checked to avoid slowing down Redis, so this should be run frequently.

| Method                   | Frequency  |  Interpretation                  |    
|--------------------------|------------|----------------------------------|
| admin_garbage_collection | < 15 mins   | Delete relics of expired names  |
| admin_promises           | < 1 second  | Execute promises                |

Promises must be run at least every second to implement delay:: streams.

### Rediz/rediz Configuration

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
- There is no temporal state (CLOBs, limit orders, bets or what-have-you), only guaranteed data delays and samples. There is no separate settlement process - everything occurs instantly upon receipt of a new data point.
- Every prediction is a distribution or joint distribution not a point estimate, and every stream is predicted.

The last statement refers to the fact that every data stream predicts itself - albeit somewhat poorly as a Dirac distribution centered on the last value. This provides a subsidy, encouraging others to improve the distributional estimate. Maintainers of streams can use mset() rather than set() to increase the subsidy up to a maximum of 0.1 USD per data point.   

### Data categories  

Rediz supports, or will support:  

- One dimensional continuous valued data (as float)
- Two dimensional geospatial data (lat/long)
- Low dimensional continuous valued data (e.g. R^3, R^4)
- High dimensional continuous valued data (e.g. R^200)   

In the last case, Rediz exploits recent results in nearest neighbor approximation. Furthermore:

- Categorical data can use float   (with some interpretation in nascent stages)
- Ordinal data can use float (with appropriate monotone transformations)

Some conveniences

### Intended future performance improvements

Moving more of the logic from Python into Lua scripts.

### Not supported

Rediz does not support UI elements, plotting and so forth.
