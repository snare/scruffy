import os
import json
import pkg_resources
import itertools
import errno

MAX_BASENAME = 16

class Environment(object):
    """An environment in which to run a program"""
    def __init__(self, spec):
        self.spec = spec
        self.basename = spec['basename']
        self.files = {}

        # apply defaults
        self.spec['dir'] = self.merge_dicts(self.spec['dir'],  {
            'create': False,
            'relative': False,
            'cleanup': False,
            'mode': 0700
        })

        # set up environment directory
        self.dir = os.path.expanduser(self.spec['dir']['path'])
        if self.spec['dir']['create']:
            try:
                os.mkdir(self.dir, self.spec['dir']['mode'])
            except OSError, e:
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
        configs = filter(lambda i: 'type' in self.spec['files'][i] and self.spec['files'][i]['type'] == 'config', self.spec['files'])
        others = filter(lambda i: i not in configs, self.spec['files'])

        for name in (configs + others):
            fspec = self.spec['files'][name]

            # apply defaults
            d = {
                'type': 'raw',
                'read': False,
                'create': False,
                'cleanup': False,
                'mode': 0700
            }
            fspec = self.merge_dicts(fspec, d)

            # add filename if one isn't provided
            if 'name' not in fspec:
                fspec['name'] = name

            # if environment var exists, override path
            if 'var' in fspec and fspec['var'] in os.environ:
                fspec['path'] = os.environ[fspec['var']]
            else:
                fspec['path'] = os.path.join(self.dir, fspec['name'])

            # substitute basename
            if self.basename:
                fspec['name'] = fspec['name'].format(basename=self.basename)

            # store updated spec
            self.spec['files'][name] = fspec

            # create file
            if 'create' in fspec and fspec['create']:
                if not os.path.isfile(fspec['path']):
                    fd = os.open(fspec['path'], os.O_WRONLY | os.O_CREAT, fspec['mode'])
                    f = os.fdopen(fd, 'w')
                    f.close()

            # load file
            if 'read' in fspec and fspec['read']:
                if fspec['type'] == 'config':
                    # load as a config file
                    self.files[name] = self.load_config(fspec)

                    print(str(self.files[name]))

                    # if there was a basename variable specified in the config, grab the contents of it
                    if 'basename_variable' in self.files[name] and self.files[name]['basename_variable'] in os.environ:
                        bn = os.environ[self.files[name]['basename_variable']].replace("/", '')
                        if len(bn) > 0:
                            if len(bn) > MAX_BASENAME:
                                bn = bn[-MAX_BASENAME:]
                            self.basename = bn
                elif fspec['type'] == 'json':
                    # load as a json file
                    self.files[name] = self.load_json(fspec)
                elif fspec['type'] == 'raw':
                    # load as raw file
                    self.files[name] = self.load_raw(fspec)
                else:
                    # no idea, just load it as raw
                    self.files[name] = self.load_raw(fspec)
            else:
                self.files[name] = self.path_to(fspec['name'])

    def load_config(self, spec):
        """Load a JSON configuration file"""

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
                config = self.parse_json(file(path).read())
            except ValueError, e:
                raise IOError("Error parsing default configuration" + e.message)

        # load local config
        try:
            local_config = self.parse_json(file(spec['path']).read())
            config = self.merge_dicts(local_config, config)
        except ValueError, e:
            raise ValueError("Error parsing local configuration: " + e.message)
        except IOError:
            pass

        return config

    def load_json(self, spec):
        """Load a JSON file"""

        return self.parse_json(file(spec['path']).read())

    def load_raw(self, spec):
        """Load a raw text file"""

        return file(spec['path']).read()

    def parse_json(self, config):
        """Parse a JSON file"""

        lines = filter(lambda x: len(x) != 0 and x.strip()[0] != '#', config.split('\n'))
        return json.loads('\n'.join(lines))

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

    def merge_dicts(self, d1, d2):
        """Merge two dictionaries"""

        # recursive merge where items in d2 override those in d1
        for k1,v1 in d1.iteritems():
            if isinstance(v1, dict) and k1 in d2.keys() and isinstance(d2[k1], dict):
                self.merge_dicts(v1, d2[k1])
            else:
                d2[k1] = v1
        return d2
