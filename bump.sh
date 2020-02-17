cd /Users/pcotton/github/rediz
cp /Users/pcotton/github/rediz/rediz/*private.py /Users/pcotton/github/rediz-tmp-config/
rm /Users/pcotton/github/rediz/rediz/*private.py 
rm /Users/pcotton/github/rediz/dist/*
python setup.py sdist bdist_wheel
rm /Users/pcotton/github/rediz/dist/
twine upload dist/*
cp /Users/pcotton/github/rediz-tmp-config/*.py /Users/pcotton/github/rediz/rediz
