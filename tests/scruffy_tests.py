from nose.tools import *
from scruffy import *
from scruffy.plugin import PluginManager

import tempfile
import subprocess
import shutil

ENV1 = []
ENV2 = []
t = None
td = None

YAML = """
thing: 123
another:
- 666
- 777
- 888
thang:
    a: 1
    b: 2
    c: 3
    d: {a: 1, b: 2, c: 3}
derp:
- {a: 1}
- {a: 2}
- {a: 3}
- {a: 4}
"""


def setup():
    global ENV1, ENV2, t, td

    # copy a config to somewhere for an absolute path test
    t = tempfile.NamedTemporaryFile(delete=False)
    d = file(os.path.join(os.getcwd(), 'tests/env1/default.cfg')).read()
    t.write(d)
    t.close()

    # copy plugins somewhere for an absolute path test
    td = tempfile.mkdtemp()
    subprocess.call('cp -R ' + os.path.join(os.getcwd(), 'tests/env1/plugins/*') + ' ' + td, shell=True)

    # set test environment variable
    os.environ['TEST_VARIABLE'] = os.path.join(os.getcwd(), 'tests/env1/the_thing.txt')

    ENV1 = Environment({
        'dir':  {
            'path': 'tests/env1',
            'create': False,
            'relative': True
        },
        'files': {
            'config1': {
                'type':     'config',
                'read':     True,
                'default':  {
                    'path':     'env1/default.cfg',
                    'rel_to':   'pkg',
                    'pkg':      'tests'
                }
            },
            'config2': {
                'type':     'config',
                'read':     True,
                'default':  {
                    'path':     'tests/env1/default.cfg',
                    'rel_to':   'pwd'
                }
            },
            'config3': {
                'type':     'config',
                'read':     True,
                'default':  {
                    'path':   t.name,
                    'rel_to': 'abs'
                }
            },
            'config4': {
                'type':     'config',
                'read':     True
            },
            'raw_file': {
                'read':     True,
                'create':   True
            },
            'json_file': {
                'type':     'json',
                'read':     True
            },
            'thing': {
                'name':     'the_thing.txt',
                'read':     True
            },
            'no_read': {
                'name':     'no_read_file',
                'read':     False
            },
            'bn_file': {
                'name':     '{basename}.txt',
                'read':     False
            },
            'var_file': {
                'name':     'no_such_file',
                'read':     True,
                'var':      'TEST_VARIABLE'
            },
            'file_rel_to_pkg': {
                'path':     'env1/the_thing.txt',
                'read':     True,
                'rel_to':   'pkg',
                'pkg':      'tests'
            },
            'file_rel_to_cwd': {
                'path':     'tests/env1/the_thing.txt',
                'read':     True,
                'rel_to':   'cwd'
            },
            'file_rel_to_abs': {
                'path':     t.name,
                'read':     True,
                'rel_to':   'abs'
            },
            'local_plugins': {
                'type':     'plugin_dir',
                'name':     'plugins'
            },
            'internal_plugins': {
                'type':     'plugin_dir',
                'path':     'env1/plugins',
                'rel_to':   'pkg',
                'pkg':      'tests'
            }
        },
        'basename': 'test'
    })
    ENV2 = Environment({
        'dir':  {
            'path': 'tests/env2',
            'create': True,
            'relative': True,
            'mode': 0700
        },
        'files': {
            'thing': {
                'type':     'raw',
                'read':     True,
                'create':   True
            },
            'local_plugins': {
                'type':     'plugin_dir',
                'name':     'plugins',
                'create':   True
            }
        },
        'basename': 'test'
    })


def teardown():
    global ENV1, ENV2
    try:
        os.remove(t.name)
    except:
        pass
    try:
        shutil.rmtree('tests/env2')
    except:
        pass
    try:
        shutil.rmtree(td)
    except:
        pass

# env 1
def test_dir():
    assert ENV1.dir == 'tests/env1'

def test_basename():
    assert ENV1.basename == 'test'

def test_raw_file_value():
    assert ENV1['raw_file'].strip() == 'raw_file value'

def test_json_file_value():
    assert ENV1['json_file']['setting1'] == 667

def test_read_write_arb_file():
    ENV1.write_file('arb_file', 'arb_file value')
    assert ENV1.read_file('arb_file').strip() == 'arb_file value'

def test_file_name():
    assert ENV1.spec['files']['thing']['name'] == 'the_thing.txt'

def test_file_basename():
    assert ENV1.spec['files']['bn_file']['name'] == 'test.txt'

def test_no_read():
    assert ENV1['no_read'] == 'tests/env1/no_read_file'

def test_var_file():
    assert ENV1.read_file('var_file') == 'thing'

def test_file_rel_to_pkg():
    assert ENV1['file_rel_to_pkg'] == 'thing'

def test_file_rel_to_cwd():
    assert ENV1['file_rel_to_cwd'] == 'thing'

def test_file_rel_to_abs():
    assert '666' in ENV1['file_rel_to_abs']

# config1
def test_config1_dict():
    assert type(ENV1['config1']) == Config

def test_config1_local_value():
    assert ENV1['config1']['setting1'] == 667

def test_config1_default_value():
    assert ENV1['config1']['setting2'] == True

def test_config1_local_value_nest():
    assert ENV1['config1']['setting3']['key1'] == 'not value'

def test_config1_default_value_nest():
    assert ENV1['config1']['setting3']['key2'] == 'value'

# config2
def test_config2_dict():
    assert type(ENV1['config2']) == Config

def test_config2_local_value():
    assert ENV1['config2']['setting1'] == 667

def test_config2_default_value():
    assert ENV1['config2']['setting2'] == True

def test_config2_local_value_nest():
    assert ENV1['config2']['setting3']['key1'] == 'not value'

def test_config2_default_value_nest():
    assert ENV1['config2']['setting3']['key2'] == 'value'

# config3
def test_config3_dict():
    assert type(ENV1['config3']) == Config

def test_config3_local_value():
    assert ENV1['config3']['setting1'] == 667

def test_config3_default_value():
    assert ENV1['config3']['setting2'] == True

def test_config3_local_value_nest():
    assert ENV1['config3']['setting3']['key1'] == 'not value'

def test_config3_default_value_nest():
    assert ENV1['config3']['setting3']['key2'] == 'value'

# config4
def test_config4_dict():
    assert type(ENV1['config4']) == Config

def test_config4_local_value():
    assert ENV1['config4']['setting1'] == 666

def test_config4_local_value_nest():
    assert ENV1['config4']['setting3']['key1'] == 'value'

# env 2
def test_create_dir():
    assert os.path.isdir(ENV2.dir)

def test_create_raw_file():
    assert os.path.isfile('tests/env2/thing')

def test_create_plugins_dir():
    assert os.path.isdir('tests/env2/plugins')

def test_plugin_load():
    assert ENV2.plugins[0].__name__ == "ThingPlugin"

def test_plugin_call():
    assert ENV2.plugins[0]().do_a_thing() == 666

def test_plugin_load_nest():
    cls = ENV2.plugins[1]
    assert cls.__name__ == "ThangPlugin"

def test_plugin_call_nest():
    assert ENV2.plugins[1]().do_a_thing() == 777

ENV3_SPEC = {
    'dir':  {
        'path': 'tests/env3',
        'create': True,
        'relative': True,
        'cleanup': True
    },
    'files': {
        'test': {
            'type':     'raw',
            'create':   True,
            'cleanup':  True
        }
    },
    'basename': 'test'
}

# env 3
def test_cleanup():
    with Environment(ENV3_SPEC) as env:
        pass
    assert not os.path.isfile('tests/env3/test')

# config object
def test_config_object():
    c = Config(YAML)
    assert type(c) == Config
    assert c.thang.d.b == 2
    assert c['thang']['d']['b'] == 2
    assert c['thang.d.b'] == 2
    assert c.derp[0] == {'a': 1}
    assert c.derp[0].a == 1

def test_config_object_set():
    c = Config()
    c.derp1 = {'a': [1,2,3], 'b': 'xxx'}
    assert c.derp1.a[0] == 1
    assert c.derp1.b == 'xxx'
    c['derp2.a.b.c'] = 123
    assert c.derp2.a.b.c == 123
    c.derp3.a.b.c = 666
    assert c.derp3.a.b.c == 666
    try:
        c.derp3.a.b.c.d = 666
        raise Exception()
    except AttributeError:
        pass
    c.derp3.b = 'x'
    c['derp4']['a']['b'] = 777
    assert c.derp4.a.b == 777
