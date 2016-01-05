import pytest
from webocr.util import run_cmd, CmdException


def test_ok():
    run_cmd('ls')


def test_ok_with_callback():
    msg = ['']

    def callback(m):
        msg[0] = m

    run_cmd('echo hola', stdout_callback=callback)
    assert msg[0] == 'hola\n'


def test_fail():
    with pytest.raises(CmdException):
        run_cmd('dfasdfad')
