import os
import inspect
import pkg_resources

from .file import File
from .plugin import PluginManager


class Directory(object):
    """
    A filesystem directory.

    A Scruffy Environment usually encompasses a number of these. For example,
    the main Directory object may represent `~/.myproject`.

    d = Directory({
        path='~/.myproject',
        create=True,
        cleanup=False,
        children=[
        ...
        ]
    })

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

        if self._path and type(self._path) == str:
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
        if type(self._path) == str:
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

    def remove(self, recursive=False):
        """
        Remove the directory.
        """
        if recursive or self._cleanup == 'recursive':
            os.removedirs(self.path)
        else:
            os.rmdir(self.path)

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
            self.remove()

    def path_to(self, path):
        """
        Find the path to something inside this directory.
        """
        return os.path.join(self.path, path)

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
        return os.listdir(self.path)

    def write(self, filename, mode='w'):
        """
        Write a file in the directory.
        """
        with open(self.path_to(filename), mode) as f:
            f.write()

    def read(self, filename):
        """
        Read a file from the directory.
        """
        with open(self.path_to(filename)) as f:
            d = f.read()
        return d

    def add(self, **kwargs):
        """
        Add objects to the directory.
        """
        for key in kwargs:
            if type(kwargs[key]) == str:
                self._children[key] = File(kwargs[key])
            else:
                self._children[key] = kwargs[key]
            self._children[key]._parent = self
            self._children[key]._env = self._env


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


class PackageFile(File):
    """
    A file whose path is relative to a Python package.
    """
    def __init__(self, path=None, create=False, cleanup=False, parent=None, package=None):
        super(PackageFile, self).__init__(path=path, create=create, cleanup=cleanup, parent=PackageDirectory(package=package))
