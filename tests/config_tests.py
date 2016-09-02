import yaml
import os

from nose.tools import *
from scruffy import *

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

# config object
def test_config_object():
    d = yaml.load(YAML)
    c = Config(data=d)
    assert type(c) == Config
    assert c.thang.d.b == 2
    assert c['thang']['d']['b'] == 2
    assert c['thang.d.b'] == 2
    assert c.derp[0] == {'a': 1}
    assert c.derp[0].a == 1
    assert c.xxx == None
    if c.xxx:
        assert False

def test_config_object_set():
    c = Config()
    c.derp1 = {'a': [1,2,3], 'b': 'xxx'}
    assert c.derp1.a[0] == 1
    assert c.derp1.b == 'xxx'
    assert type(c.derp1.b) == str
    c['derp2.a.b.c'] = 123
    assert c.derp2.a.b.c == 123
    c.derp3.a.b.c = 666
    assert c.derp3.a.b.c == 666
    try:
        c.derp3.a.b.c.d = 666
        raise Exception()
    except Exception as e:
        if type(e) != AttributeError:
            raise
    c.derp3.b = 'x'
    c['derp4']['a']['b'] = 777
    assert c.derp4.a.b == 777
    assert type(c.derp4) == ConfigNode
    assert type(c.derp4.a.b) == int

def test_config_object_update():
    d = yaml.load(YAML)
    c = Config(defaults=d)
    c.update(options={'derp.0.a': 666, 'derp.0.b': 777})
    assert c.derp[0].a == 666
    assert c.derp[0].b == 777
    assert type(c.derp) == ConfigNode
    c.derp[1].a = 123
    c.derp[1].b = 234
    assert c.derp[1] == {'a': 123, 'b': 234}
    c.update(data={'thang': {'d': {'b': 666}}})
    assert c.thang.d == {'a': 1, 'b': 666, 'c': 3}
    c2 = Config({'thang': {'d': {'b': 777}}})
    c.update(c2)
    assert c.thang.d == {'a': 1, 'b': 777, 'c': 3}

def test_config_object_reset():
    d = yaml.load(YAML)
    c = Config(defaults=d)
    c.update(options={'derp.0.a': 666, 'derp.0.b': 777})
    c.reset()
    assert c == d

def test_config_file():
    c = ConfigFile(defaults='tests/env1/json_config')
    c.load()
    c.update(options={'derp.0.a': 666, 'derp.0.b': 777})
    assert c.derp[0].a == 666
    assert c.derp[0].b == 777
    assert c.setting1 == 667
    assert c.setting3.key1 == "not value"
    c = ConfigFile('tests/env1/json_config', load=True)
    assert c.setting1 == 667
    assert c.setting3.key1 == "not value"
    c.update(options={'derp.0.a': 666, 'derp.0.b': 777})
    assert c.derp[0].a == 666
    assert c.derp[0].b == 777

def test_config_env():
    os.environ['__SC_TEST.A.A.A'] = 'AAAA'
    os.environ['__SC_TEST.A.A.B'] = '1234'
    os.environ['__SC_TEST.A.A.C'] = '1234.5678'
    os.environ['__SC_TEST.A.A.D'] = '0x1234'
    c = ConfigEnv()
    assert c == {'test': {'a': {'a': {'a': 'AAAA', 'c': 1234.5678, 'b': 1234, 'd': 4660}}}}
    c = ConfigFile('tests/env1/config1', load=True, apply_env=True)
    assert c.test == {'a': {'a': {'a': 'AAAA', 'c': 1234.5678, 'b': 1234, 'd': 4660}}}

def test_config_yaml():
    c = ConfigFile('tests/env1/yaml_config', defaults='tests/env1/default.cfg', load=True)
    assert c.setting1 == 666
    assert c.setting2 == True
    assert c.setting3.key1 == "value"

def test_config_file_with():
    with ConfigFile('tests/env1/yaml_config', defaults='tests/env1/default.cfg') as c:
        assert c.setting1 == 666
        assert c.setting2 == True
        assert c.setting3.key1 == "value"

def test_config_applicator():
    ap = ConfigApplicator(ConfigFile('tests/env1/yaml_config', load=True))
    assert ap.apply('/some/path/{config:setting1}/hurr/{config:setting3.key1}.txt') == '/some/path/666/hurr/value.txt'
    try:
        ap.apply('{config:xxx')
        assert False
    except KeyError:
        assert True
