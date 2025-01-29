"""
Plugin
------

Classes for representing and loading plugins.
"""
import os
import importlib
import six


class PluginRegistry(type):
    """
    Metaclass that registers any classes using it in the `plugins` array
    """
    plugins = []
    def __init__(cls, name, bases, attrs):
        if name != 'Plugin' and cls.__name__ not in map(lambda x: x.__name__, PluginRegistry.plugins):
            PluginRegistry.plugins.append(cls)


@six.add_metaclass(PluginRegistry)
class Plugin(object):
    """
    Top-level plugin class, using the PluginRegistry metaclass.

    All plugin modules must implement a single subclass of this class. This
    subclass will be the class collected in the PluginRegistry, and should
    contain references to any other resources required within the module.
    """


class PluginManager(object):
    """
    Loads plugins which are automatically registered with the PluginRegistry
    class, and provides an interface to the plugin collection.
    """
    def load_plugins(self, directory):
        """
        Loads plugins from the specified directory.

        `directory` is the full path to a directory containing python modules
        which each contain a subclass of the Plugin class.

        There is no criteria for a valid plugin at this level - any python
        module found in the directory will be loaded. Only modules that
        implement a subclass of the Plugin class above will be collected.

        The directory will be traversed recursively.
        """
        # walk directory
        for filename in os.listdir(directory):
            # path to file
            filepath = os.path.join(directory, filename)

            # if it's a file, load it
            modname, ext = os.path.splitext(filename)
            if os.path.isfile(filepath) and ext == '.py':
                spec = importlib.util.spec_from_file_location(modname, filepath)
                if spec:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)

            # if it's a directory, recurse into it
            if os.path.isdir(filepath):
                self.load_plugins(filepath)

    @property
    def plugins(self):
        return PluginRegistry.plugins