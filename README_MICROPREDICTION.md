# microprediction

Collective microprediction client leveraging www.microprediction.com 

    pip install microprediction 
    
# Reading 

It is possible to retrieve most quantities at www.microprediction.com with direct web calls.

    import requests
    lagged_values = mr.get('lagged_values::cop.json')
    lagged_values = requests.get('https://www.microprediction.com/live/lagged_values::cop.json').json()

However the reader client adds a little convenience. 

    from microprediction import MicroReader
    mr = MicroReader()
 
    summary       = mr.get_summary('cop.json')
    current_value = mr.get('cop.json')
    lagged_values = mr.get_lagged_values('cop.json') 
    lagged_times  = mr.get_lagged_times('cop.json')
    
Approximate crowd cumulative distribution function:
    
    cdf = mr.get_cdf('cop.json',delay=70)
    
Quarantined value
    
    cdf = mr.get_delayed('cop.json',delay=70)
    
# Write client

Used to submit predictions or request predictions by creating a data stream. 

### Obtaining a write_key (muid.org)

As explained at https://vimeo.com/397352413 you need to mine a MUID to obtain write privileges, such as submitting predictions. 
You can cut and paste this bash command into terminal:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/microprediction/muid/master/examples/mine_from_venv.sh)"

or using the MUID library...
    
    $pip install muid
    $python3
    >>> import muid
    >>> muid.mine(skip_intro=True)
   
Once you have a key:   

    from microprediction import MicroWriter
    mw = MicroWriter(write_key='53e6fbba-2dcd-486c-a4ab-14759db58dde')  # Sub in your own key 
    
## Submitting predictions 
    
    scenarios = [ i*0.001 for i in range(mw.num_predictions) ] 
    mw.submit(name='cop.json',values=scenarios)    

There is no difference when predicting derived streams. For example:

    my_scenarios = sorted(list(np.random.randn(mw.num_predictions))
    mw.submit(name="z1~airp-06820.json", write_key="ce169feeb3565b282d50a850dc62e0db", values = my_scenarios, delay=15)

## Stream name rules 

 - Must end in .json 
 - Contain alphanumeric, hyphens, underscores, colons (discouraged) and at most one period.
 - Must not contain double colon. 


# Submitting data to be predicted

You can use the writer to create a stream of live data that clever algorithms and humans can predict.

### Qualifying

You can write a new stream if:

    len(muid.animal(write_key))  >  official minimum length     # You have a hard to find MUID
    
and 

    mw.balance(write_key)  >   official minimum balance         # Not broke
    
See https://www.microprediction.com/config.json for the current values of min_len and min_balance. See
https://vimeo.com/397352413 for explanation of muid.animal(), also called the difficulty. You can always
chec by entering a URL like http://www.muid.org/validate/fb74baf628d43892020d803614f91f29 

### Updating the current value

Set current value. 

    prctl = mw.put(name='mystream.json',value=3.14157) 

By default this returns a percentile so you know how surprising the data point is. 


### Distribution of future values

You can retrieve quarantined crowd cumulative distribution function:

     cdf = mr.get_cdf('cop.json',delay=mr.delays[0],values=[0,0.5])
     
where the delay parameter, in seconds, acts as a prediction horizon. 
         
### Logs

Limited logging information may be retrieved:
    
    get_errors()
    
or

    error_log = requests.get('https://www.microprediction.com/live/errors::53e6fbba-2dcd-486c-a4ab-14759db58dde.json').json()
 
