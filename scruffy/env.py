import os
import yaml
import pkg_resources
import itertools
import errno

from .plugin import PluginManager
from .config import ConfigNode

MAX_BASENAME = 16


class Environment(object):
    """An environment in which to run a program"""
    def __init__(self, spec):
        self.spec = spec
        self.basename = spec['basename']
        self.files = {}
        self.plugin_mgr = PluginManager()

        # apply defaults
        self.spec['dir'] = merge_dicts(self.spec['dir'],  {
            'create': False,
            'relative': False,
            'cleanup': False,
            'mode': 448 # 0700
        })

        # set up environment directory
        self.dir = os.path.expanduser(self.spec['dir']['path'])
        if self.spec['dir']['create']:
            try:
                os.mkdir(self.dir, self.spec['dir']['mode'])
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        # setup files
        self.init_files()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.clean_up()

    def __getitem__(self, key):
        return self.files[key]

    def init_files(self):
        """Initialise files"""

        # initialise files, loading any config files first to ensure that any basename etc changes have applied
        configs = list(filter(lambda i: 'type' in self.spec['files'][i] and self.spec['files'][i]['type'] == 'config', self.spec['files']))
        others = list(filter(lambda i: i not in configs, self.spec['files']))

        for name in (configs + others):
            fspec = self.spec['files'][name]

            # apply defaults
            d = {
                'type': 'raw',      # raw file
                'read': False,      # don't read
                'create': False,    # don't create
                'cleanup': False,   # don't clean up
                'mode': 448,        # 0700
                'rel_to': 'dir'     # relative to environment directory
            }
            fspec = merge_dicts(fspec, d)

            # if we didn't get a name, use the name of the dictionary
            if 'name' not in fspec:
                fspec['name'] = name

            # substitute basename
            if self.basename:
                fspec['name'] = fspec['name'].format(basename=self.basename)

            # if this file doesn't have a path specified, use the name
            if 'path' not in fspec:
                # otherwise we use the 'path' field provided
                fspec['path'] = fspec['name']

            # if environment var exists in this fspec then use it to override the path
            if 'var' in fspec and fspec['var'] in os.environ:
                fspec['path'] = os.environ[fspec['var']]
            else:
                # otherwise update the path based on the 'rel_to' field
                if fspec['rel_to'] == 'pkg' and 'pkg' in fspec:
                    # relative to a given package, and package is specified
                    fspec['path'] = pkg_resources.resource_filename(fspec['pkg'], fspec['path'])
                elif fspec['rel_to'] == 'pwd' or fspec['rel_to'] == 'cwd':
                    # relative to the current working directory
                    fspec['path'] = os.path.join(os.getcwd(), fspec['path'])
                elif fspec['rel_to'] == 'abs':
                    # absolute path has been provided, don't update it
                    pass
                else:
                    # relative to the environment directory (the default)
                    fspec['path'] = os.path.join(self.dir, fspec['path'])

            # store updated spec
            self.spec['files'][name] = fspec

            # create file
            if 'create' in fspec and fspec['create']:
                if fspec['type'] == 'plugin_dir':
                    # create the plugin directory if it doesn't exist
                    if not os.path.exists(fspec['path']):
                        os.mkdir(fspec['path'])
                elif not os.path.exists(fspec['path']):
                    # otherwise if it's a normal file of some kind and doesn't exist, create it
                    fd = os.open(fspec['path'], os.O_WRONLY | os.O_CREAT, fspec['mode'])
                    f = os.fdopen(fd, 'w')
                    f.close()

            # load file
            if 'read' in fspec and fspec['read']:
                if fspec['type'] == 'config':
                    # load as a config file
                    self.files[name] = self.load_config(fspec)

                    # if there was a basename variable specified in the config, grab the contents of it
                    if 'basename_variable' in self.files[name] and self.files[name]['basename_variable'] in os.environ:
                        bn = os.environ[self.files[name]['basename_variable']].replace("/", '')
                        if len(bn) > 0:
                            if len(bn) > MAX_BASENAME:
                                bn = bn[-MAX_BASENAME:]
                            self.basename = bn
                elif fspec['type'] in ['json', 'yaml']:
                    # load as a yaml file
                    self.files[name] = self.load_yaml(fspec)
                elif fspec['type'] == 'raw':
                    # load as raw file
                    self.files[name] = self.load_raw(fspec)
                elif fspec['type'] == 'plugin_dir':
                    # this is a plugin directory, ignore it here as we'll load it below
                    pass
                else:
                    # no idea, just load it as raw
                    self.files[name] = self.load_raw(fspec)
            else:
                self.files[name] = fspec['path']

            # load plugins
            if fspec['type'] == 'plugin_dir':
                self.load_plugins(fspec)

    def load_config(self, spec):
        """Load a JSON/YAML configuration file"""

        # load default config
        config = {}
        if 'default' in spec:
            # find where the default configuration is
            if spec['default']['rel_to'] == 'pkg':
                path = pkg_resources.resource_filename(spec['default']['pkg'], spec['default']['path'])
            elif spec['default']['rel_to'] == 'pwd':
                path = os.path.join(os.getcwd(), spec['default']['path'])
            elif spec['default']['rel_to'] == 'abs':
                path = spec['default']['path']

            # load it
            try:
                config = self.parse_yaml(open(path).read())
            except ValueError as e:
                raise IOError("Error parsing default configuration" + e.message)

        # load local config
        try:
            local_config = self.parse_yaml(open(spec['path']).read())
            config = merge_dicts(local_config, config)
        except ValueError as e:
            raise ValueError("Error parsing local configuration: " + e.message)
        except IOError:
            pass

        return ConfigNode(data=config)

    def load_json(self, spec):
        """Load a JSON file"""

        return self.parse_yaml(file(spec['path']).read())

    def load_yaml(self, spec):
        """Load a YAML file"""

        return self.parse_yaml(file(spec['path']).read())

    def load_raw(self, spec):
        """Load a raw text file"""

        return file(spec['path']).read()

    def load_plugins(self, spec):
        """Load plugins"""

        self.plugin_mgr.load_plugins(spec['path'])

    def parse_json(self, data):
        """Parse a JSON file"""

        return self.parse_yaml(data)

    def parse_yaml(self, data):
        """Parse a YAML file"""

        return yaml.load(data.replace('\t', '    '))

    def read_file(self, name):
        """Read a file within the environment"""

        # get a file spec
        spec = self.file_spec(name)

        # read file
        return file(spec['path']).read()

    def write_file(self, name, data):
        """Read a file within the environment"""

        # open file
        spec = self.file_spec(name)
        f = open(spec['path'], 'w+')

        # truncate the file if we're not appending
        if not 'append' in spec or 'append' in spec and not spec['append']:
            f.truncate()

        # write file
        f.write(data)
        f.close()

    def path_to(self, filename):
        """Return the path to a file within the environment"""

        return os.path.join(self.dir, filename)

    def file_spec(self, name):
        """Return a file spec for the specified name"""

        if name in self.spec['files']:
            spec = self.spec['files'][name]
        else:
            spec = {'name': name, 'type': 'raw', 'path':self.path_to(name)}

        return spec

    def clean_up(self):
        """Clean up the environment"""

        # remove any files that need to be cleaned up
        for name in self.spec['files']:
            fspec = self.spec['files'][name]
            if 'cleanup' in fspec and fspec['cleanup']:
                os.unlink(self.path_to(name))

        # remove the directory if necessary
        if self.spec['dir']['cleanup']:
            os.rmdir(self.dir)


    @property
    def plugins(self):
        return self.plugin_mgr.plugins


def merge_dicts(d1, d2):
    """Merge two dictionaries"""

    # recursive merge where items in d2 override those in d1
    for k1,v1 in d1.items():
        if isinstance(v1, dict) and k1 in d2.keys() and isinstance(d2[k1], dict):
            merge_dicts(v1, d2[k1])
        else:
            d2[k1] = v1
    return d2
