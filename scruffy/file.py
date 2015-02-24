import os
import yaml
import copy
import logging
import logging.config


class File(object):
    """
    Represents a file on the filesystem.

    Usually encapsulated in a Directory.
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

    def apply_config(self, applicator):
        """
        Replace any config tokens with values from the config.
        """
        if type(self._fpath) == str:
            self._fpath = applicator.apply(self._fpath)

    def create(self):
        """
        Create the file if it doesn't already exist.
        """
        open(self.path, 'a').close()

    def remove(self):
        """
        Remove the file.
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
    def __init__(self, path=None, logger=None, loggers=[], formatter={}, format=None,  *args, **kwargs):
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
        if type(self._formatter) == str:
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

