from setuptools import setup

setup(
    name="scruffington",
    version="0.3.1",
    author="snare",
    author_email="snare@ho.ax",
    description=("The janitor"),
    license="MIT",
    keywords="scruffy",
    url="https://github.com/snare/scruffy",
    packages=['scruffy'],
    install_requires=['pyyaml', 'sqlalchemy', 'six'],
)
