

# Rediz implementation notes 

More details on internal conventions 

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

We refer the reader to www.microprediction.com for more information about the motivation for Rediz.

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

 
