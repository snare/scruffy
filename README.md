# scruffy

*Scruffy. The Janitor.*

Scruffy is a simple framework for managing the environment in which a Python-based tool runs. It handles the loading of configuration files, creation of temporary pid/state/socket files, etc.

Scruffy is used by [Voltron](https://github.com/snarez/voltron) and [Calculon](https://github.com/snarez/calculon). Richo suggested pulling it out into its own package, and it seemed like a good idea to write more documentation and tests than actual code.

## Usage Example

Say you're writing a simple command-line tool for keeping track of the ducks in your collection. Let's call it `duckman`. `duckman` is installed with `setuptools`, which installs a package to your Python `site-packages` and creates a console entry point script. The package directory looks something like this:
	
	duckman
	duckman/__init__.py
	duckman/classification.py
	duckman/flat.py
	duckman/upright.py
	duckman/default.cfg

`default.cfg` is a JSON file containing the default configuration:

	{
		"duck_pref": 	"upright",
		"duck_db": 		"duckman.db"
	}

The user decides they much prefer flat ducks (naturally). In order to override this configuration, the user creates a directory `~/.duckman` and a file `config` inside containing:

	{
		"duck_pref": 	"flat"
	}

`duckman` also requires a lock file so other instances know that this `duckman` is doing his thing.

In order to load the configuration file, apply it on top of the defaults, create the lock file and clean it up at exit, the following code is used in `duckman`:

	from scruffy import Environment

	ENV = Environment({
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

The configuration from `~/.duckman/config` is loaded and defaults applied, and the `ENV` variable can then be used to access the config data like this:

	ENV['config']['duck_pref']

If you want to create another file within the environment directory (`~/.duckman`):

	ENV.write_file('temp', 'some data')

For more complicated examples see the included unit tests, [Voltron](https://github.com/snarez/voltron) and [Calculon](https://github.com/snarez/calculon).