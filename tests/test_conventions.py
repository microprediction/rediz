from rediz.conventions import RedizConventions

def test_vanity_key():
    write_key = RedizConventions.vanity_key('abcd')
    if write_key:
        code = RedizConventions.hash(write_key)
        print("code is "+code)
        print("write_key is "+write_key)