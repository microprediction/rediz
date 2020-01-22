cd /Users/pcotton/github/rediz
rm /Users/pcotton/github/rediz/dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
