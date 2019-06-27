"""
Config
------

Classes for loading and accessing configuration data.
"""
from __future__ import unicode_literals
import copy
import os
import ast
import yaml
import re

from six import string_types
from .file import File


class ConfigNode(object):
    """
    Represents a Scruffy config object.

    Can be accessed as a dictionary, like this:

        >>> config['top-level-section']['second-level-property']

    Or as a dictionary with a key path, like this:

        >>> config['top_level_section.second_level_property']

    Or as an object, like this:

        >>> config.top_level_section.second_level_property
    """
    def __init__(self, data={}, defaults={}, root=None, path=None):
        super(ConfigNode, self).__init__()
        self._root = root
        if not self._root:
            self._root = self
        self._path = path
        self._defaults = defaults
        self._data = copy.deepcopy(self._defaults)
        self.update(data)

    def __getitem__(self, key):
        c = self._child(key)
        v = c._get_value()
        if type(v) in [dict, list, type(None)]:
            return c
        else:
            return v

    def __setitem__(self, key, value):
        container, last = self._child(key)._resolve_path(create=True)
        container[last] = value

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super(ConfigNode, self).__setattr__(key, value)
        else:
            self[key] = value

    def __str__(self):
        return str(self._get_value())

    def __repr__(self):
        return str(self._get_value())

    def __int__(self):
        return int(self._get_value())

    def __float__(self):
        return float(self._get_value())

    def __lt__(self, other):
        return self._get_value() < other

    def __le__(self, other):
        return self._get_value() <= other

    def __le__(self, other):
        return self._get_value() <= other

    def __eq__(self, other):
        return self._get_value() == other

    def __ne__(self, other):
        return self._get_value() != other

    def __gt__(self, other):
        return self._get_value() > other

    def __ge__(self, other):
        return self._get_value() >= other

    def __contains__(self, key):
        return key in self._get_value()

    def __nonzero__(self):
        return self._get_value() != None

    def __bool__(self):
        return self._get_value() != None

    def items(self):
        return self._get_value().items()

    def keys(self):
        return self._get_value().keys()

    def __iter__(self):
        return self._get_value().__iter__()

    def _child(self, path):
        """
        Return a ConfigNode object representing a child node with the specified
        relative path.
        """
        if self._path:
            path = '{}.{}'.format(self._path, path)
        return ConfigNode(root=self._root, path=path)

    def _resolve_path(self, create=False):
        """
        Returns a tuple of a reference to the last container in the path, and
        the last component in the key path.

        For example, with a self._value like this:

        {
            'thing': {
                'another': {
                    'some_leaf': 5,
                    'one_more': {
                        'other_leaf': 'x'
                    }
                }
            }
        }

        And a self._path of: 'thing.another.some_leaf'

        This will return a tuple of a reference to the 'another' dict, and
        'some_leaf', allowing the setter and casting methods to directly access
        the item referred to by the key path.
        """
        # Split up the key path
        if isinstance(self._path, string_types):
            key_path = self._path.split('.')
        else:
            key_path = [self._path]

        # Start at the root node
        node = self._root._data
        nodes = [self._root._data]

        # Traverse along key path
        while len(key_path):
            # Get the next key in the key path
            key = key_path.pop(0)

            # See if the test could be an int for array access, if so assume it is
            try:
                key = int(key)
            except:
                pass

            # If the next level doesn't exist, create it
            if create:
                if type(node) == dict and key not in node:
                    node[key] = {}
                elif type(node) == list and type(key) == int and len(node) < key:
                    node.append([None for i in range(key-len(node))])

            # Store the last node and traverse down the hierarchy
            nodes.append(node)
            try:
                node = node[key]
            except TypeError:
                if type(key) == int:
                    raise IndexError(key)
                else:
                    raise KeyError(key)

        return (nodes[-1], key)

    def _get_value(self):
        """
        Get the value represented by this node.
        """
        if self._path:
            try:
                container, last = self._resolve_path()
                return container[last]
            except KeyError:
                return None
            except IndexError:
                return None
        else:
            return self._data

    def update(self, data={}, options={}):
        """
        Update the configuration with new data.

        This can be passed either or both `data` and `options`.

        `options` is a dict of keypath/value pairs like this (similar to
        CherryPy's config mechanism:

            >>> c.update(options={
            ...     'server.port': 8080,
            ...     'server.host': 'localhost',
            ...     'admin.email': 'admin@lol'
            ... })

        `data` is a dict of actual config data, like this:

            >>> c.update(data={
            ...     'server': {
            ...         'port': 8080,
            ...         'host': 'localhost'
            ...     },
            ...     'admin': {
            ...         'email': 'admin@lol'
            ...     }
            ... })
        """
        # Handle an update with a set of options like CherryPy does
        for key in options:
            self[key] = options[key]

        # Merge in any data in `data`
        if isinstance(data, ConfigNode):
            data = data._get_value()
        update_dict(self._get_value(), data)

    def reset(self):
        """
        Reset the config to defaults.
        """
        self._data = copy.deepcopy(self._defaults)

    def to_dict(self):
        """
        Generate a plain dictionary.
        """
        return self._get_value()


class Config(ConfigNode):
    """
    Config root node class. Just for convenience.
    """


class ConfigEnv(ConfigNode):
    """
    Config based on based on environment variables.
    """
    def __init__(self, prefix='SCRUFFY', *args, **kwargs):
        super(ConfigEnv, self).__init__(*args, **kwargs)

        # build options dictionary from environment variables starting with the prefix
        options = {}
        for key in [v for v in os.environ if v.startswith('__SC_') or v.startswith(prefix + '_')]:
            try:
                val = ast.literal_eval(os.environ[key])
            except:
                val = os.environ[key]
            options[key.replace('__SC_', '').replace(prefix + '_', '').lower()] = val

        # update config with the values we've found
        self.update(options=options)


class ConfigFile(Config, File):
    """
    Config based on a loaded YAML or JSON file.
    """
    def __init__(self, path=None, defaults=None, load=False, apply_env=False, env_prefix='SCRUFFY', *args, **kwargs):
        self._loaded = False
        self._defaults_file = defaults
        self._apply_env = apply_env
        self._env_prefix = env_prefix
        Config.__init__(self)
        File.__init__(self, path=path, *args, **kwargs)

        if load:
            self.load()

    def load(self, reload=False):
        """
        Load the config and defaults from files.
        """
        if reload or not self._loaded:
            # load defaults
            if self._defaults_file and isinstance(self._defaults_file, string_types):
                self._defaults_file = File(self._defaults_file, parent=self._parent)
            defaults = {}
            if self._defaults_file:
                defaults = yaml.safe_load(self._defaults_file.read().replace('\t', '    '))

            # load data
            data = {}
            if self.exists:
                data = yaml.safe_load(self.read().replace('\t', '    '))

            # initialise with the loaded data
            self._defaults = defaults
            self._data = copy.deepcopy(self._defaults)
            self.update(data=data)

            # if specified, apply environment variables
            if self._apply_env:
                self.update(ConfigEnv(self._env_prefix))

            self._loaded = True

        return self

    def save(self):
        """
        Save the config back to the config file.
        """
        self.write(yaml.safe_dump(self._data))

    def prepare(self):
        """
        Load the file when the Directory/Environment prepares us.
        """
        self.load()


class ConfigApplicator(object):
    """
    Applies configs to other objects.
    """
    def __init__(self, config):
        self.config = config

    def apply(self, obj):
        """
        Apply the config to an object.
        """
        if isinstance(obj, str):
            return self.apply_to_str(obj)

    def apply_to_str(self, obj):
        """
        Apply the config to a string.
        """
        toks = re.split('({config:|})', obj)
        newtoks = []
        try:
            while len(toks):
                tok = toks.pop(0)
                if tok == '{config:':
                    # pop the config variable, look it up
                    var = toks.pop(0)
                    val = self.config[var]

                    # if we got an empty node, then it didn't exist
                    if type(val) == ConfigNode and val == None:
                        raise KeyError("No such config variable '{}'".format(var))

                    # add the value to the list
                    newtoks.append(str(val))

                    # pop the '}'
                    toks.pop(0)
                else:
                    # not the start of a config block, just append it to the list
                    newtoks.append(tok)
            return ''.join(newtoks)
        except IndexError:
            pass

        return obj


def update_dict(target, source):
    """
    Recursively merge values from a nested dictionary into another nested
    dictionary.

    For example:

    >>> target = {
    ...     'thing': 123,
    ...     'thang': {
    ...         'a': 1,
    ...         'b': 2
    ...     }
    ... }
    >>> source = {
    ...     'thang': {
    ...         'a': 666,
    ...         'c': 777
    ...     }
    ... }
    >>> update_dict(target, source)
    >>> target
    {
        'thing': 123,
        'thang': {
            'a': 666,
            'b': 2,
            'c': 777
        }
    }
    """
    for k,v in source.items():
        if isinstance(v, dict) and k in target and isinstance(source[k], dict):
            update_dict(target[k], v)
        else:
            target[k] = v

