


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

No permissions are required to read.

### Future scenarios (coming soon)

Any user can contribute to Monte Carlo scenarios describing possible future values. The prefixes refer to market-like mechanisms used under the hood which provide incentive for contributors to provide
samples which individually or collectively map the joint distribution accurately.

| Example                           | Interpretation                        |
|-----------------------------------|---------------------------------------|
| nano:60:air-pressure-06820.json   | Listing of 1 minute ahead scenarios   |
| near:15:air-pressure-06820.json   | Listing of 15 second ahead scenarios  |

At present the choices of prefix are:

| Prefix | Name         | Interpretation and properties                              |
|--------|--------------|------------------------------------------------------------|
| nano   | Nanomutuel   | A relative compensation scheme analogous to a pari-mutuel clearing mechanism, but extending to high dimensions, nano-markets reward contributors who provide samples in previously under-sampled regions in the joint distribution. A log-wealth maximizing investor has incentive to contribute paths that reflect her unbiased assessment of the joint distribution.  |
| near   | Nearest Squared Error     | Based on high performers in an absolute compensation scheme where the criteria is squared distance between the realized outcome and the nearest scenario. In the case where a contributor adjusts model parameters and then supplies samples from that model, it can be shown that minimizing expected squared distance to the nearest point is equivalent to Maximum Likelihood estimation of the model parameters.

See https://arxiv.org/abs/1809.09087 for a proof of the statement made about Nearest Squared Error. Calculations are performed by the library threeza.py  

### Point estimate predictions

Subject to careful statistical interpretation, point estimates can be
directly read at name/values with the following patterns:

| Example                                   | Interpretation              |
|-------------------------------------------|-----------------------------|
| mean::nano:60:air-pressure-06820.json     | Mean 1 minute forecast      |
| mean::near:600:air-pressure-06820.json    | Mean 10 minute forecast     |

### Public methods

Listing of methods, permission and candidate economic model

| Method        | Key(s)? |  Cost |  Interpretation                  |    
|---------------|---------|-------|----------------------------------|
| set           | Yes     |  1    | Create/modify value at one name  |
| mset          | Yes     |  1000 | Create/modify many name/values   |
| new           | No      |  1    | Create a name w/o providing key  |
| mnew          | No      |  1000 | Create many names w/o keys       |
| card          | No      |  0    | Count of all names               |
| exists        | No      |  0    | Count names that exist in a list |
| get           | No      |  0    | Retrieve a value (one name)      |
| mget          | No      |  0    | Retrieve from many names         |
| delete        | Yes     |  0    | Delete and relinquish ownership  |
| mdelete       | Yes     |  0    | Relinquish many names            |
| subscribe     | Yes     |  1    | Subscribe a name to a source     |
| unsubscribe   | Yes     |  0    | Subscribe a name to many sources |
| subscriptions | Yes     |  0    | List of a name's subscriptions   |

### Administrative methods

The following methods must be run periodically

| Method                   | Frequency  |  Interpretation                  |    
|--------------------------|------------|----------------------------------|
| admin_garbage_collection | < 15 mins   | Delete relics of expired names  |
| admin_promises           | < 1 second  | Execute promises                |
