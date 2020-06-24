from getjson import getjson

def test_getjson():
    data = getjson('https://config.microprediction.org/config.json')
    assert isinstance(data,dict)
