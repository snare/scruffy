import yaml

from nose.tools import *
from scruffy import Config

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
    assert type(c.derp4) == Config
    assert type(c.derp4.a.b) == int

def test_config_object_update():
    d = yaml.load(YAML)
    c = Config(defaults=d)
    c.update(options={'derp.0.a': 666, 'derp.0.b': 777})
    assert c.derp[0].a == 666
    assert c.derp[0].b == 777
    assert type(c.derp) == Config
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