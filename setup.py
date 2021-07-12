import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="rediz",
    version="0.14.1",
    description="Powering community nowcasts at www.microprediction.org",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/microprediction/rediz",
    author="microprediction",
    author_email="pcotton@intechinvestments.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["rediz"],
    test_suite='pytest',
    tests_require=['pytest', 'microconventions', 'fakeredis'],
    include_package_data=True,
    install_requires=["microconventions>=0.5.1", "fakeredis", "getjson", "redis", "sortedcontainers", "numpy",
                      "pymorton", "scipy", "pathlib"],
    entry_points={
        "console_scripts": [
            "rediz=rediz.__main__:main",
        ]
    },
)
