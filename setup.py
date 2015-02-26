from setuptools import setup

setup(
    name = "scruffy",
    version = "0.3",
    author = "snare",
    author_email = "snare@ho.ax",
    description = ("The janitor"),
    license = "Buy snare a beer",
    keywords = "scruffy",
    url = "https://github.com/snare/scruffy",
    packages=['scruffy'],
    install_requires = ['pyyaml', 'sqlalchemy', 'six'],
)
