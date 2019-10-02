from setuptools import setup

with open("README.rst", "r") as fp:
    long_description = fp.read()

setup(
    name="scruffington",
    version="0.3.8.1",
    author="snare",
    author_email="snare@ho.ax",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    description=("The janitor"),
    license="MIT",
    keywords="scruffy",
    url="https://github.com/snare/scruffy",
    packages=['scruffy'],
    install_requires=['pyyaml', 'six'],
)
