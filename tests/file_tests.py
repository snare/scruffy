import os
import logging
import nose

import scruffy
from scruffy import *


def safe_unlink(path):
    try:
        os.unlink(path)
    except:
        pass


def test_file():
    p = '/tmp/scruffy_test_file.txt'
    f = File(p)
    safe_unlink(p)
    assert not os.path.exists(p)
    f.create()
    assert os.path.exists(p)
    assert f.name == 'scruffy_test_file.txt'
    assert f.ext == '.txt'
    assert f.path == '/tmp/scruffy_test_file.txt'
    f.write('xyz')
    assert f.exists
    assert f.content == 'xyz'
    f.remove()
    assert not f.exists
    assert str(f) == '/tmp/scruffy_test_file.txt'


def test_prepare_cleanup():
    p = '/tmp/scruffy_test_file'
    f = File(p, create=True, cleanup=True)
    safe_unlink(p)
    assert not os.path.exists(p)
    f.prepare()
    assert os.path.exists(p)
    f.cleanup()
    assert not os.path.exists(p)


def test_file_with():
    p = '/tmp/scruffy_test_file'
    safe_unlink(p)
    assert not os.path.exists(p)
    with File(p, create=True, cleanup=True):
        assert os.path.exists(p)
    assert not os.path.exists(p)


def test_lock_file():
    p = '/tmp/scruffy_test_file'
    safe_unlink(p)
    assert not os.path.exists(p)
    with LockFile(p):
        assert os.path.exists(p)
    assert not os.path.exists(p)
    f = File(p)
    f.create()
    try:
        with LockFile(p):
            assert False
    except:
        assert True
    f.remove()
    assert not os.path.exists(p)


def test_log_file():
    log = logging.getLogger()
    log.handlers = []
    f = LogFile('/tmp/test.log')
    try:
        f.remove()
    except:
        pass
    f.prepare()
    assert f.path == '/tmp/test.log'
    assert len(log.handlers) == 1
    assert isinstance(log.handlers[0], logging.FileHandler)
    log.info('test')
    with open(f.path) as fi:
        assert fi.read().strip() == "test"
    f.remove()


def test_package_file():
    f = PackageFile('xxx', package='scruffy')
    assert f.path == os.path.join(os.getcwd(), 'scruffy/xxx')


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
    d.create()
    d.add(File('xxx'))
    assert d.xxx.path == '/tmp/scruffy_test/xxx'
    d.xxx.create()
    assert type(d.list()[0]) == File
    assert str(d.list()[0]) == '/tmp/scruffy_test/xxx'


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
    d.write('temp_file', 'xxx')
    assert d.read('temp_file') == 'xxx'


def test_directory_file_with():
    with Directory('tests/env1', thing=File('raw_file')) as d:
        assert type(d.thing) == File
        assert d.thing.content.strip() == 'raw_file value'


def test_directory_add_file():
    d = Directory('tests/env1')
    x = d.add(File('xxx'))
    assert d.xxx.name == 'xxx'
    assert x == d.xxx
    x = d.add('yyy')
    assert d.yyy.name == 'yyy'
    assert x == d.yyy


@nose.tools.raises(TypeError)
def test_directory_add_file_fail():
    d = Directory('tests/env1')
    d.add(1)
