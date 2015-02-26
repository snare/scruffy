import sys

from setuptools import setup

setup(
    name = "duckman",
    version = "0.1",
    author = "snare",
    author_email = "snare@ho.ax",
    description = ("Ya thrust yer pelvis HUAGHH"),
    license = "Buy snare a beer",
    keywords = "duckman",
    url = "https://github.com/snare/scruffy",
    packages=['duckman'],
    entry_points = {
        'console_scripts': ['duckman = duckman:main']
    },
    install_requires = ['scruffington']
)
