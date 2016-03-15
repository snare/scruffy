import os
import logging

from scruffy import *


def safe_unlink(path):
    try:
        os.unlink(path)
    except:
        pass

def test_file():
    p = '/tmp/scruffy_test_file'
    f = File(p)
    safe_unlink(p)
    assert not os.path.exists(p)
    f.create()
    assert os.path.exists(p)

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
