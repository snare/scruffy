import os

import scruffy
from scruffy import *


def test_directory():
    d = Directory('tests/env1')
    p = '/tmp/scruffy_test'
    assert os.path.exists(d.path)
    try:
        os.removedirs(p)
    except:
        pass
    with Directory(p, cleanup=True) as d:
        assert os.path.exists(p)
        assert d.exists
        assert d.path_to('x') == os.path.join(p, 'x')
    assert not os.path.exists(p)

def test_plugin_directory():
    scruffy.plugin.PluginRegistry.plugins = []
    assert len(PluginManager().plugins) == 0
    d = PluginDirectory('tests/env1/plugins')
    d.load()
    assert len(PluginManager().plugins) == 2

def test_package_directory():
    d = PackageDirectory()
    assert d._base == os.path.join(os.getcwd(), 'tests')
    d = PackageDirectory(package='scruffy')
    assert d._base == os.path.join(os.getcwd(), 'scruffy')
    d = PackageDirectory('xxx', package='scruffy')
    assert d._base == os.path.join(os.getcwd(), 'scruffy')
    assert d.path == os.path.join(os.getcwd(), 'scruffy/xxx')

def test_nested_package_plugin():
    d = PluginDirectory('env1/plugins', parent=PackageDirectory())
    assert d.path == os.path.join(os.getcwd(), 'tests/env1/plugins')
    scruffy.plugin.PluginRegistry.plugins = []
    assert len(PluginManager().plugins) == 0
    d.load()
    assert len(PluginManager().plugins) == 2

def test_directory_config():
    d = Directory('tests/env1', config=ConfigFile('json_config'))
    d.prepare()
    assert type(d.config) == ConfigFile
    assert d.config.setting1 == 667

def test_directory_file():
    d = Directory('tests/env1', thing=File('raw_file'))
    d.prepare()
    assert type(d.thing) == File
    assert d.thing.content.strip() == 'raw_file value'

def test_directory_file_with():
    with Directory('tests/env1', thing=File('raw_file')) as d:
        assert type(d.thing) == File
        assert d.thing.content.strip() == 'raw_file value'
