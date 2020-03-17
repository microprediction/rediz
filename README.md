

# Rediz / Microprediction

Server and client packages enabling open community microprediction at www.microprediction.com.  

### Overview 

The python packages called "microprediction" (user client library) and "rediz" (system implementation using redis as transport) are demonstrated at www.microprediction.com, where they 
make it easy for anyone who needs a live source of data predicted to receive help from clever humans and self-navigating time series algorithms.  They do this by:

 - Obtaining a write_key of sufficient strength using www.muid.org 
 - Using the write_key to update a live quantity, such as https://www.microprediction.com/live/cop.json
 - Repeating often.  

They can then access history (e.g. https://www.microprediction.com/live/lagged::cop.json) and predictions (e.g. https://www.microprediction.com/cdf/cop.json). This is an easy way to 
normalize data and perform anomaly detection. Over time it may garner other insights such as assessment of the predictive value of the data stream the identities of streams that
might be causally related. 

This setup is especially well suited to collective prediction of civic data streams such as transport, water, electricity, public supply chain indicators or the spread of infectious diseases. 
  

### Client README (microprediction package)

https://github.com/microprediction/rediz/blob/master/README_MICROPREDICTION.md

### Server README (rediz package)

 - https://github.com/microprediction/rediz/blob/master/README_REDIZ.md 
 - https://github.com/microprediction/rediz/blob/master/README_REDIZ_DETAILS.md


