"""
File
----

Classes for representing and performing operations on files and directories.
"""
from __future__ import unicode_literals
import os
from six import string_types
import yaml
import copy
import logging
import logging.config
import inspect
import pkg_resources
import shutil

from .plugin import PluginManager


class File(object):
    """
    Represents a file that may or may not exist on the filesystem.

    Usually encapsulated by a Directory or an Environment.
    """
    def __init__(self, path=None, create=False, cleanup=False, parent=None):
        super(File, self).__init__()
        self._parent = parent
        self._fpath = path
        self._create = create
        self._cleanup = cleanup

        if self._fpath:
            self._fpath = os.path.expanduser(self._fpath)

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, type, value, traceback):
        self.cleanup()

    def __str__(self):
        return self.path

    def apply_config(self, applicator):
        """
        Replace any config tokens in the file's path with values from the config.
        """
        if isinstance(self._fpath, string_types):
            self._fpath = applicator.apply(self._fpath)

    def create(self):
        """
        Create the file if it doesn't already exist.
        """
        open(self.path, 'a').close()

    def remove(self):
        """
        Remove the file if it exists.
        """
        if self.exists:
            os.unlink(self.path)

    def prepare(self):
        """
        Prepare the file for use in an Environment or Directory.

        This will create the file if the create flag is set.
        """
        if self._create:
            self.create()

    def cleanup(self):
        """
        Clean up the file after use in an Environment or Directory.

        This will remove the file if the cleanup flag is set.
        """
        if self._cleanup:
            self.remove()

    @property
    def path(self):
        """
        Get the path to the file relative to its parent.
        """
        if self._parent:
            return os.path.join(self._parent.path, self._fpath)
        else:
            return self._fpath

    @property
    def name(self):
        """
        Get the file name.
        """
        return os.path.basename(self.path)

    @property
    def ext(self):
        """
        Get the file's extension.
        """
        return os.path.splitext(self.path)[1]

    @property
    def content(self):
        """
        Property for the content of the file.
        """
        return self.read()

    @property
    def exists(self):
        """
        Whether or not the file exists.
        """
        return self.path and os.path.exists(self.path)

    def read(self):
        """
        Read and return the contents of the file.
        """
        with open(self.path) as f:
            d = f.read()
        return d

    def write(self, data, mode='w'):
        """
        Write data to the file.

        `data` is the data to write
        `mode` is the mode argument to pass to `open()`
        """
        with open(self.path, mode) as f:
            f.write(data)


class LogFile(File):
    """
    A log file to configure with Python's logging module.
    """
    def __init__(self, path=None, logger=None, loggers=[], formatter={}, format=None, *args, **kwargs):
        super(LogFile, self).__init__(path=path, *args, **kwargs)
        self._create = True
        self._cleanup = True
        self._formatter = formatter
        self._format = format

        if logger:
            self._loggers = [logger]
        else:
            self._loggers = loggers

    def prepare(self):
        """
        Configure the log file.
        """
        self.configure()

    def configure(self):
        """
        Configure the Python logging module for this file.
        """
        # build a file handler for this file
        handler = logging.FileHandler(self.path, delay=True)

        # if we got a format string, create a formatter with it
        if self._format:
            handler.setFormatter(logging.Formatter(self._format))

        # if we got a string for the formatter, assume it's the name of a
        # formatter in the environment's config
        if isinstance(self._format, string_types):
            if self._env and self._env.config.logging.dict_config.formatters[self._formatter]:
                d = self._env.config.logging.dict_config.formatters[self._formatter].to_dict()
                handler.setFormatter(logging.Formatter(**d))
        elif type(self._formatter) == dict:
            # if it's a dict it must be the actual formatter params
            handler.setFormatter(logging.Formatter(**self._formatter))

        # add the file handler to whatever loggers were specified
        if len(self._loggers):
            for name in self._loggers:
                logging.getLogger(name).addHandler(handler)
        else:
            # none specified, just add it to the root logger
            logging.getLogger().addHandler(handler)


class LockFile(File):
    """
    A file that is automatically created and cleaned up.
    """
    def __init__(self, *args, **kwargs):
        super(LockFile, self).__init__(*args, **kwargs)
        self._create = True
        self._cleanup = True

    def create(self):
        """
        Create the file.

        If the file already exists an exception will be raised
        """
        if not os.path.exists(self.path):
            open(self.path, 'a').close()
        else:
            raise Exception("File exists: {}".format(self.path))


class YamlFile(File):
    """
    A yaml file that is parsed into a dictionary.
    """
    @property
    def content(self):
        """
        Parse the file contents into a dictionary.
        """
        return yaml.safe_load(self.read())


class JsonFile(YamlFile):
    """
    A json file that is parsed into a dictionary.
    """


class PackageFile(File):
    """
    A file whose path is relative to a Python package.
    """
    def __init__(self, path=None, create=False, cleanup=False, parent=None, package=None):
        super(PackageFile, self).__init__(path=path, create=create, cleanup=cleanup, parent=PackageDirectory(package=package))


class Directory(object):
    """
    A filesystem directory.

    A Scruffy Environment usually encompasses a number of these. For example,
    the main Directory object may represent `~/.myproject`.

    >>> d = Directory({
    ...     path='~/.myproject',
    ...     create=True,
    ...     cleanup=False,
    ...     children=[
    ...     ...
    ...     ]
    ... })

    `path` can be either a string representing the path to the directory, or
    a nested Directory object. If a Directory object is passed as the `path`
    its path will be requested instead. This is so Directory objects can be
    wrapped in others to inherit their properties.
    """
    def __init__(self, path=None, base=None, create=True, cleanup=False, parent=None, **kwargs):
        self._path = path
        self._base = base
        self._create = create
        self._cleanup = cleanup
        self._pm = PluginManager()
        self._children = {}
        self._env = None
        self._parent = parent

        if self._path and isinstance(self._path, string_types):
            self._path = os.path.expanduser(self._path)

        self.add(**kwargs)

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, type, value, traceback):
        self.cleanup()

    def __getitem__(self, key):
        return self._children[key]

    def __getattr__(self, key):
        return self._children[key]

    def apply_config(self, applicator):
        """
        Replace any config tokens with values from the config.
        """
        if isinstance(self._path, string_types):
            self._path = applicator.apply(self._path)

        for key in self._children:
            self._children[key].apply_config(applicator)

    @property
    def path(self):
        """
        Return the path to this directory.
        """
        p = ''

        if self._parent and self._parent.path:
            p = os.path.join(p, self._parent.path)
        if self._base:
            p = os.path.join(p, self._base)
        if self._path:
            p = os.path.join(p, self._path)

        return p

    def create(self):
        """
        Create the directory.

        Directory will only be created if the create flag is set.
        """
        if not self.exists:
            os.mkdir(self.path)

    def remove(self, recursive=True, ignore_error=True):
        """
        Remove the directory.
        """
        try:
            if recursive or self._cleanup == 'recursive':
                shutil.rmtree(self.path)
            else:
                os.rmdir(self.path)
        except Exception as e:
            if not ignore_error:
                raise e

    def prepare(self):
        """
        Prepare the Directory for use in an Environment.

        This will create the directory if the create flag is set.
        """
        if self._create:
            self.create()
        for k in self._children:
            self._children[k]._env = self._env
            self._children[k].prepare()

    def cleanup(self):
        """
        Clean up children and remove the directory.

        Directory will only be removed if the cleanup flag is set.
        """
        for k in self._children:
            self._children[k].cleanup()

        if self._cleanup:
            self.remove(True)

    def path_to(self, path):
        """
        Find the path to something inside this directory.
        """
        return os.path.join(self.path, str(path))

    @property
    def exists(self):
        """
        Check if the directory exists.
        """
        return os.path.exists(self.path)

    def list(self):
        """
        List the contents of the directory.
        """
        return [File(f, parent=self) for f in os.listdir(self.path)]

    def write(self, filename, data, mode='w'):
        """
        Write to a file in the directory.
        """
        with open(self.path_to(str(filename)), mode) as f:
            f.write(data)

    def read(self, filename):
        """
        Read a file from the directory.
        """
        with open(self.path_to(str(filename))) as f:
            d = f.read()
        return d

    def add(self, *args, **kwargs):
        """
        Add objects to the directory.
        """
        for key in kwargs:
            if isinstance(kwargs[key], string_types):
                self._children[key] = File(kwargs[key])
            else:
                self._children[key] = kwargs[key]
            self._children[key]._parent = self
            self._children[key]._env = self._env

        added = []
        for arg in args:
            if isinstance(arg, File):
                self._children[arg.name] = arg
                self._children[arg.name]._parent = self
                self._children[arg.name]._env = self._env
            elif isinstance(arg, string_types):
                f = File(arg)
                added.append(f)
                self._children[arg] = f
                self._children[arg]._parent = self
                self._children[arg]._env = self._env
            else:
                raise TypeError(type(arg))

        # if we were passed a single file/filename, return the File object for convenience
        if len(added) == 1:
            return added[0]
        if len(args) == 1:
            return args[0]


class PluginDirectory(Directory):
    """
    A filesystem directory containing plugins.
    """
    def prepare(self):
        """
        Preparing a plugin directory just loads the plugins.
        """
        super(PluginDirectory, self).prepare()
        self.load()

    def load(self):
        """
        Load the plugins in this directory.
        """
        self._pm.load_plugins(self.path)


class PackageDirectory(Directory):
    """
    A filesystem directory relative to a Python package.
    """
    def __init__(self, path=None, package=None, *args, **kwargs):
        super(PackageDirectory, self).__init__(path=path, *args, **kwargs)

        # if we weren't passed a package name, walk up the stack and find the first non-scruffy package
        if not package:
            frame = inspect.currentframe()
            while frame:
                if frame.f_globals['__package__'] != 'scruffy':
                    package = frame.f_globals['__package__']
                    break
                frame = frame.f_back

        # if we found a package, set the path directory to the base dir for the package
        if package:
            self._base = pkg_resources.resource_filename(package, '')
        else:
            raise Exception('No package found')
