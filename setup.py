import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="rediz",
    version="0.2.16",
    description="Open access to competing prediction algorithms",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/microprediction/rediz",
    author="microprediction",
    author_email="info@3za.org",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["rediz"],
    test_suite='pytest',
    tests_require=['pytest'],
    include_package_data=True,
    install_requires=["muid","microprediction","fakeredis","redis","sortedcontainers","numpy","aiohttp","pymorton","scipy","pathlib","cachetools","flask","flask_restx"],
    entry_points={
        "console_scripts": [
            "rediz=rediz.__main__:main",
        ]
     },
     )
