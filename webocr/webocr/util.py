import collections
import errno
import functools
import logging
import os
import requests
import signal
import socket
from subprocess import Popen, PIPE

from tornado import gen
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest

from ._compat import to_bytes, to_string


class CmdException(Exception):
    pass

CmdResult = collections.namedtuple('CmdResult',
                                   'cmd stdout stderr status_code')


def current_dir():
    return os.path.abspath(os.path.dirname(__file__))


def run_cmd(cmd, shell=True, env=None, cwd=None, stdout_callback=None,
            stderr_callback=None):
    child = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=cwd, env=env)
    output = ''
    while child.poll() is None:
        # This blocks until it receives a newline.
        line = to_string(child.stdout.readline())
        if line:
            if stdout_callback is not None:
                stdout_callback(line)
            output += line
    # When the subprocess terminates there might be unconsumed output
    # that still needs to be processed.
    o = to_string(child.stdout.read())
    if o:
        if stdout_callback is not None:
            stdout_callback(o)
        output += o

    err = to_string(child.stderr.read())
    if err:
        if stderr_callback is not None:
            stderr_callback(err)

    rc = child.returncode
    cmd_result = CmdResult(cmd=cmd, stdout=output, stderr=err, status_code=rc)
    if rc != 0:
        raise CmdException(repr(cmd_result))


def download_file(url, filename, chunk_size=1024):
    with open(filename, 'wb') as file:
        response = requests.get(url, stream=True)
        if not response.ok:
            raise Exception('Error downloading file: {}'.format(response))
            # Something went wrong
        for block in response.iter_content(chunk_size):
            file.write(block)


# python 2 doesn't have it
class ConnectionRefusedError(Exception):
    pass


@gen.coroutine
def wait_for(fn, fn_args=[], fn_kwargs={},
             timeout=60, wait_time=0.2):
    loop = ioloop.IOLoop.current()
    tic = loop.time()

    success = False
    while loop.time() - tic < timeout:
        try:
            yield fn(*fn_args, **fn_kwargs)
        except ConnectionRefusedError as e:
            logging.debug(str(e))
            yield gen.Task(loop.add_timeout, loop.time() + wait_time)
        except HTTPError as e:
            logging.debug(str(e))
            yield gen.Task(loop.add_timeout, loop.time() + wait_time)
        except OSError as e:
            logging.debug(str(e))
            yield gen.Task(loop.add_timeout, loop.time() + wait_time)
        else:
            success = True
            break

    if not success:
        raise TimeoutError()


@gen.coroutine
def wait_for_http(host, port=80, path='', headers={},
                  timeout=60, wait_time=0.2):
    http_client = AsyncHTTPClient()
    req = HTTPRequest("http://{}:{}/{}".format(host, port, path),
                      headers=headers)
    yield wait_for(http_client.fetch, [req],
                   timeout=timeout, wait_time=wait_time)


@gen.coroutine
def wait_for_tcp(host, port, timeout=60, wait_time=0.2):
    @gen.coroutine
    def connect_tcp():
        s = MySocket(msg_len=5)
        s.connect(host, port)
        s.mysend(to_bytes('hello'))
        raise gen.Return()
    yield wait_for(connect_tcp, timeout=timeout, wait_time=wait_time)


class MySocket(object):
    '''demonstration class only
      - coded for clarity, not efficiency
    '''

    def __init__(self, sock=None, msg_len=65536):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.msg_len = msg_len

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, msg):
        totalsent = 0
        while totalsent < self.msg_len:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def myreceive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < self.msg_len:
            chunk = self.sock.recv(min(self.msg_len - bytes_recd, 2048))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return ''.join(chunks)


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator
