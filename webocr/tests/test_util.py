import logging

import pytest

from webocr.app import App
from webocr.config import Config
from webocr.util import \
    wait_for_http, wait_for_tcp, current_dir, TimeoutError

logging.basicConfig(level=logging.DEBUG)

'''
Important. http server needs to be running on port 2345:
$ python2 -m SimpleHTTPServer 2345
'''


@pytest.fixture
def app():
    c = Config('.')
    c.from_pyfile('{}/../dev-conf.py'.format(current_dir()))
    a = App(c)
    return a.app


@pytest.mark.gen_test
def test_http():
    yield wait_for_http(host='localhost', port=2345)


@pytest.mark.gen_test(timeout=30)
def test_http_timeout():
    with pytest.raises(TimeoutError):
        yield wait_for_http(host='localhost', port=2222, timeout=2)


@pytest.mark.gen_test
def test_tcp():
    yield wait_for_tcp(host='localhost', port=2345)


@pytest.mark.gen_test(timeout=30)
def test_tcp_timeout():
    with pytest.raises(TimeoutError):
        yield wait_for_tcp(host='localhost', port=2222, timeout=2)
