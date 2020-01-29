


## REDIZ

Used to create a public read, write permission-based shared remote database hosting live data at www.3za.org. Conveniences provided include history, subscription, delay and market-like mechanisms intended to facilitate collectivized short term prediction of public data. The instance at www.3za.org exposes public methods enumerated below via a combination of free and minimal cost APIs. The minimal cost APIs allow sponsors of prediction streams to pay for crowd-based prediction of public data of civic, scientific or commercial significance.  

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

Listing of methods, permission and candidate economic model

| Method        | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| set           | Yes     |  1    | Create/modify value at one name  | Y     |
| mset          | Yes     |  1000 | Create/modify many name/values   | Y     |
| new           | No      |  1    | Create a name w/o providing key  | Y     |
| mnew          | No      |  1000 | Create many names w/o keys       | Y     |
| card          | No      |  0    | Count of all names               | Y     |
| exists        | No      |  0    | Count names that exist in a list | Y     |
| get           | No      |  0    | Retrieve a value (one name)      | Y     |
| mget          | No      |  0    | Retrieve from many names         | Y     |
| delete        | Yes     |  0    | Delete and relinquish ownership  | Y     |
| mdelete       | Yes     |  0    | Relinquish many names            | Y     |
| subscribe     | Yes     |  1    | Subscribe a name to a source     | Y     |
| unsubscribe   | Yes     |  0    | Subscribe a name to many sources | Y     |
| subscriptions | Yes     |  0    | List of a name's subscriptions   | Y     |
| link          | Yes     |  1    | Suggest a (causal) link          | N     |                     
| unlink        | Yes     |  0    | Delete a causal link             | N     |
| links         | Yes     |  0    | List outgoing links              | N     |

In addition the following shortcuts are provided:

| Method        | Key(s)? |  Cost |  Interpretation                  | Done? |   
|---------------|---------|-------|----------------------------------|-------|
| predict       | Yes     |  1    | Equivalent to set then link      | N     |                      
| mpredict      | Yes     |  1000 | Equivalent to mset + mlink       | N     |



### Administrative methods

The following methods must be run periodically

| Method                   | Frequency  |  Interpretation                  |    
|--------------------------|------------|----------------------------------|
| admin_garbage_collection | < 15 mins   | Delete relics of expired names  |
| admin_promises           | < 1 second  | Execute promises                |
