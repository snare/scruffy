

class ConfigNode(object):
    """
    Represents a Scruffy config object.

    Can be accessed as a dictionary, like this:

        config['top-level-section']['second-level-property']

    Or as a dictionary with a key path, like this:

        config['top_level_section.second_level_property']

    Or as an object, like this:

        config.top_level_section.second_level_property
    """
    def __init__(self, data={}, root=None, path=None):
        self._root = root
        if not self._root:
            self._root = self
        self._path = path
        self._data = data

    def __getitem__(self, key):
        return self._child(key)

    def __setitem__(self, key, value):
        # Resolve the path to the specified key
        container, last = self._child(key)._resolve_path(create=True)

        # Set the value
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
        key_path = self._path.split('.')

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
                # XXX: Maybe add automagic conversion of nodes to dicts on indexing if we do shit like this
                #   thing.x = 1
                #   thing.x.y = 2

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