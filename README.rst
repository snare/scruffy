Scruffy
=======

.. image:: https://img.shields.io/travis/snare/scruffy.svg
    :target: https://travis-ci.org/snare/scruffy

.. image:: https://img.shields.io/pypi/format/scruffington.svg
    :target: https://pypi.python.org/pypi/scruffington

.. image:: https://readthedocs.org/projects/scruffy/badge/?version=stable
    :target: http://scruffy.readthedocs.org/en/stable/

.. image:: https://readthedocs.org/projects/scruffy/badge/?version=latest
    :target: http://scruffy.readthedocs.org/en/latest/


*Scruffy. The Janitor.*

Scruffy is a framework for taking care of a bunch of boilerplate in Python apps. It handles the loading of configuration files, the loading and management of plugins, and the management of other filesystem resources such as temporary files and directories, log files, etc.

A typical use case for Scruffy is a command-line Python tool with some or all of the following requirements:

* Read a set of configuration defaults
* Read a local configuration file and apply it on top of the defaults
* Allow overriding some configuration options with command line flags or at runtime
* Load a core set of Python-based plugins
* Load a set of user-defined Python-based plugins
* Generate log files whose name, location and other logging settings are based on configuration
* Store application state between runs in a file or database

Scruffy is used by [Voltron](https://github.com/snare/voltron) and [Calculon](https://github.com/snare/calculon).

Installation
------------

A standard python setup script is included.

    $ python setup.py install

This will install the Scruffy package wherever that happens on your system.

Alternately, Scruffy can be installed with `pip` from PyPi (where it's called `scruffington`, because I didn't check for a conflict before I named it).

    $ pip install scruffington

Quick start
-----------

Config
~~~~~~

Load a user config file, and apply it on top of a set of defaults loaded from inside the Python package we're currently running from.

*thingy.yaml*:

.. code:: yaml

    some_property:  1
    other_property: a thing

*thingy.py*:

.. code:: python

    from scruffy import ConfigFile

    c = ConfigFile('thingy.yaml', load=True,
        defaults=File('defaults.yaml', parent=PackageDirectory())
    )

    print("c.some_property == {c.some_property}".format(c=c))
    print("c.other_property == {c.other_property}".format(c=c))

Run it:

::

    $ python thingy.py
    c.some_property == 1
    c.other_property == a thing

Plugins
~~~~~~~

Load some plugins.

*~/.thingy/plugins/example.py*:

.. code:: python

    from scruffy import Plugin

    class ExamplePlugin(Plugin):
        def do_a_thing(self):
            print('{}.{} is doing a thing'.format(__name__, self.__class__.__name__))

*thingy.py*:

.. code:: python

    from scruffy import PluginDirectory, PluginRegistry

    pd = PluginDirectory('~/.thingy/plugins')
    pd.load()

    for p in PluginRegistry.plugins:
        print("Initialising plugin {}".format(p))
        p().do_a_thing()

Run it:

::

    $ python thingy.py
    Initialising plugin <class 'example.ExamplePlugin'>
    example.ExamplePlugin is doing a thing

Logging
~~~~~~~

Scruffy's `LogFile` class will do some configuration of Python's `logging` module.

*log.py*:

.. code:: python

    import logging
    from scruffy import LogFile

    log = logging.getLogger('main')
    log.setLevel(logging.INFO)
    LogFile('/tmp/thingy.log', logger='main').configure()

    log.info('Hello from log.py')

*/tmp/thingy.log*:

::

    Hello from log.py

Environment
~~~~~~~~~~~

Scruffy's `Environment` class ties all the other stuff together. The other classes can be instantiated as named children of an `Environment`, which will load any `Config` objects, apply the configs to the other objects, and then prepare the other objects.

*~/.thingy/config*:

.. code:: yaml

    log_dir:    /tmp/logs
    log_file:   thingy.log

*env.py*:

.. code:: python

    from scruffy import *

    e = Environment(
        main_dir=Directory('~/.thingy', create=True,
            config=ConfigFile('config', defaults=File('defaults.yaml', parent=PackageDirectory())),
            lock=LockFile('lock')
            user_plugins=PluginDirectory('plugins')
        ),
        log_dir=Directory('{config:log_dir}', create=True
            LogFile('{config:log_file}', logger='main')
        ),
        pkg_plugins=PluginDirectory('plugins', parent=PackageDirectory())
    )

License
-------

See LICENSE file. If you use this and don't hate it, buy me a beer at a conference some time.

Credits
-------

Props to [richo](http://github.com/richo). Flat duck pride.