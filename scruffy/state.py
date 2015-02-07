import os
import yaml
from collections import defaultdict


class State(object):
    """
    A program's state.

    Contains a dictionary that can be periodically saved and restored at startup.

    Maybe later this will be subclassed with database connectors and whatnot,
    but for now it'll just save to a yaml file.
    """
    def __init__(self, path):
        self.path = path
        self.d = defaultdict(lambda: None)
        self.load()

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        self.save()

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key, value):
        self.d[key] = value

    def save(self):
        """
        Save the state to a file.
        """
        with open(self.path, 'w') as f:
            f.write(yaml.dump(dict(self.d)))

    def load(self):
        """
        Load a saved state file.
        """
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                self.d = yaml.load(f.read().replace('\t', ' '*4))

    def cleanup(self):
        """
        Clean up the saved state.
        """
        if os.path.exists(self.path):
            os.remove(self.path)