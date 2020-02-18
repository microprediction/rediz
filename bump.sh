cd /Users/pcotton/github/rediz
rm /Users/pcotton/github/rediz/rediz/*private.py
cp /Users/pcotton/github/rediz-mutilated-config/*.py /Users/pcotton/github/rediz/rediz
rm /Users/pcotton/github/rediz/dist/*
python setup.py sdist bdist_wheel
rm /Users/pcotton/github/rediz/dist/
twine upload dist/*
rm /Users/pcotton/github/rediz/rediz/*private.py
cp /Users/pcotton/github/rediz-tmp-config/*.py /Users/pcotton/github/rediz/rediz
