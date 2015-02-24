import tempfile
import subprocess
import shutil
import yaml
import os

from nose.tools import *

import scruffy
from scruffy import Environment, ConfigFile, Directory
from scruffy.plugin import PluginManager


def test_environment_config():
    e = Environment(config=ConfigFile('tests/env1/json_config'))
    assert e.config.setting1 == 667
    assert e.config.setting3.key1 == 'not value'

def test_environment_config_default():
    e = Environment(config=ConfigFile('tests/env1/json_config', defaults='tests/env1/default.cfg'))
    assert e.config.setting1 == 667
    assert e.config.setting2 == True
    assert e.config.setting3.key1 == 'not value'
    assert e.config.setting3.key2 == 'value'

def test_environment_directory_config():
    e = Environment(
        dir=Directory('tests/env1',
            config=ConfigFile('json_config', defaults='default.cfg'),
            otherconfig=ConfigFile('json_config2')
        )
    )
    assert e.config.setting1 == 667
    assert e.config.setting2 == True
    assert e.config.setting3.key1 == 'not value'
    assert e.config.setting3.key2 == 'value'
    assert e.dir.config.setting1 == 667
    assert e.dir.config.setting2 == True
    assert e.dir.config.setting3.key1 == 'not value'
    assert e.dir.config.setting3.key2 == 'value'
    assert e.dir.otherconfig.setting1 == 888
    assert e.dir.otherconfig.setting2 == True

def test_environment_full():
    e = Environment(
        dir=Directory('tests/env1',
            config=ConfigFile('json_config', defaults='default.cfg'),
            otherconfig=ConfigFile('json_config2')
        ),
        config_var_dir=Directory('{config:somedir}', create=True),
        somefile=scruffy.File('{config:somefile}'),
        string_dir='/tmp/scruffy_string_dir'
    )
    assert e.config_var_dir.path == '/tmp/scruffy_test_dir'
    assert os.path.exists('/tmp/scruffy_test_dir')
    assert e.somefile.content.strip() == 'thing'
    e.string_dir.create()
    assert os.path.exists('/tmp/scruffy_string_dir')
    e.string_dir.remove()
