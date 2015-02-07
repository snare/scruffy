# scruffy

*Scruffy. The Janitor.*

Scruffy is a simple framework for managing the environment in which a Python-based tool runs. It handles the loading of configuration files, creation of temporary pid/state/socket files, and the loading and management of plugins.

Scruffy is used by [Voltron](https://github.com/snarez/voltron) and [Calculon](https://github.com/snarez/calculon). Richo suggested pulling it out into its own package, and it seemed like a good idea to write more documentation and tests than actual code.

## Configuration

Scruffy provides a `Config` class to represent a hierarchical configuration. This configuration might represented on disk as a JSON or YAML document.

This class can be used standalone without Scruffy's `Environment` class.

`Config` can be initalised with a `dict`, like this:

	>>> c = Config({'option1': 'value', 'option2': 'value'})

This object acts a lot like a Python `dict` from here on out:

	>>> c
	{'option2': 'value', 'option1': 'value'}
	>>> c['option1']
	value
	>>> type(c)
	<class 'scruffy.config.Config'>

But it can also be accessed like an object, using attributes to access data:

	>>> c = Config()
	>>> c.something = 123
	>>> c.someguy.email = 'someguy@hurr'
	>>> c.someguy.name = 'Some Guy'
	>>> c
	{'something': 123, 'someguy': {'email': 'someguy@hurr', 'name': 'Some Guy'}}
	>>> c.someguy
	{'email': 'someguy@hurr', 'name': 'Some Guy'}
	>>> c.someguy.name
	Some Guy

Properties that don't exist will return `None`:

	>>> c.someproperty
	None

Nested properties that don't currently exist can also be accessed, like this:

	>>> c = Config()
	>>> c
	{}
	>>> c.a.b.c.d
	None
	>>> c.a.b.c.d = 1
	>>> c.a.b.c.d
	1
	>>> c
	{'a': {'b': {'c': {'d': 1}}}}

`Config` objects can be created with a default configuration, which it can be reset to with the `reset()` method:

	>>> c = Config(defaults={'option2': 'value', 'option1': 'value'})
	>>> c
	{'option2': 'value', 'option1': 'value'}
	>>> c.option1 = 'xxx'
	>>> c
	{'option2': 'value', 'option1': 'xxx'}
	>>> c.reset()
	>>> c
	{'option2': 'value', 'option1': 'value'}	

Multiple config properties can be updated with a call to the `update()` method. The `options` paramater can contain a flat dictionary of properties keyed by "key paths" into the config object, like this:

	>>> options = {
	...     'option1': 'xxx',
	...     'section.subsection.item1': 123,
	...     'section.subsection.item2': 666
	... }
	>>> c.update(options=options)
	>>> c
	{'section': {'subsection': {'item2': 666, 'item1': 123}}, 'option2': 'value', 'option1': 'xxx'}

Or a nested dictionary can be passed instead, using the `data` parameter:

	>>> c.reset()
	>>> c
	{'option2': 'value', 'option1': 'value'}
	>>> c.update(data={'section': {'subsection': {'item2': 666, 'item1': 123}}})
	>>> c
	{'section': {'subsection': {'item2': 666, 'item1': 123}}, 'option2': 'value', 'option1': 'value'}

This method can be used to apply multiple levels of configuration on top of other levels. For example a default set of config options, a local configuration, command-line overrides, and then runtime configuration changes.

## Environment

Scruffy's `Environment` class manages the program's environment. It is responsible for initialising directories, loading configuration files, etc.

Say you're writing a simple command-line tool for keeping track of the ducks in your collection. Let's call it `duckman`. `duckman` is installed with `setuptools`, which installs a package to your Python `site-packages` and creates a console entry point script. The package directory looks something like this:
	
	duckman
	duckman/__init__.py
	duckman/classification.py
	duckman/flat.py
	duckman/upright.py
	duckman/default.cfg

`default.cfg` is a YAML (or JSON) file containing the default configuration:

	duck_pref:	upright
	duck_db:	duckman.db

The user decides they much prefer flat ducks (naturally). In order to override this configuration, the user creates a directory `~/.duckman` and a file `config` inside containing:

	duck_pref:	flat

`duckman` also requires a lock file so other instances know that this `duckman` is doing his thing.

In order to load the configuration file, apply it on top of the defaults, create the lock file and clean it up at exit, the following code is used in `duckman`:

	from scruffy import Environment

	env = Environment({
	    'dir':  {
	        'path': '~/.duckman',					# path to our environment directory
	        'create': True							# create it if it doesn't exist, we need to store the lockfile
	    },
	    'files': {
	        'config': {
	            'type':     'config',				# special case of json (applies default stuff below)
	            'read':     True,					# read config at initialisation
	            'default':  {
	                'path':     'default.cfg',		# path to default config file
	                'rel_to':   'pkg',				# base directory to which the path is relative (can also be "pwd" and "abs")
	                'pkg':      'duckman'			# the name of the package where the default config resides
	            }
	        },
	        'lock': {
	            'type':     'raw',
	            'read':     False,					# don't bother reading the contents, it's just a lock file
	            'create':   True,					# create it during initialisation
	            'cleanup':	True					# remove it during cleanup
	        }
	    },
	    'basename': 'duckman'						# voodoo? (not relevant for this example)
	})

The configuration from `~/.duckman/config` is loaded and defaults applied, and the `env` variable can then be used to access the config data like this:

	env['config']['duck_pref']

	or

	config = env['config']
	config.duck_pref

If you want to create another file within the environment directory (`~/.duckman`):

	env.write_file('temp', 'some data')

For more complicated examples see the included unit tests, [Voltron](https://github.com/snare/voltron) and [Calculon](https://github.com/snare/calculon).