import os

from nose.tools import *
from scruffy.state import State

STATE_FILE = 'test.state'

def setup():
    State(STATE_FILE).cleanup()

def test_state():
    s = State(STATE_FILE)
    s['xxx'] = 1
    assert s.d == {'xxx': 1}
    s.save()
    assert os.path.exists(STATE_FILE)
    s2 = State(STATE_FILE)
    assert s2['xxx'] == 1
    s.d = {}
    s.load()
    assert s['xxx'] == 1
    s.cleanup()
    assert not os.path.exists(STATE_FILE)

def test_with():
    with State(STATE_FILE) as s:
        s['yyy'] = 123
    s2 = State(STATE_FILE)
    assert s['yyy'] == 123
    s.cleanup()