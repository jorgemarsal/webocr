import json
import sys

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

if sys.version_info[0] == 2:
    from .util import ConnectionRefusedError
from .util import to_string


class TaskServerError(Exception):
    pass


class TaskServer(object):
    pass


class CeleryRestTornadoTaskServer(TaskServer):
    def __init__(self, config):
        super(TaskServer, self).__init__()
        self.config = config
        self.http_client = AsyncHTTPClient()

    @gen.coroutine
    def get_status(self, task_id):
        req = HTTPRequest(url='{}/{}'.format(
            self.config['CELERY_API_ENDPOINT'],
            'tasks/result/{}/'.format(task_id)))
        try:
            rsp = yield self.http_client.fetch(req)
        except ConnectionRefusedError as e:
            raise TaskServerError(str(e))
        except HTTPError as e:
            raise TaskServerError(str(e))
        else:
            if rsp.code < 200 or rsp.code >= 300:
                raise TaskServerError(str(rsp))
            try:
                rsp_d = json.loads(to_string(rsp.body))
            except ValueError as e:
                raise TaskServerError(str(e))
            raise gen.Return(rsp_d)

    @gen.coroutine
    def create(self, service, config):
        req = HTTPRequest(
            url='{}/{}'.format(
                config['CELERY_API_ENDPOINT'],
                'apply-async/webocr.create_service/'),
            method='POST',
            body=json.dumps({
                "args": [service, config]
            }))
        try:
            rsp = yield self.http_client.fetch(req)
        except ConnectionRefusedError as e:
            raise TaskServerError(str(e))
        except HTTPError as e:
            raise TaskServerError(str(e))
        else:
            if rsp.code < 200 or rsp.code >= 300:
                raise TaskServerError(
                    'Task server returned {}'.format(rsp.code))
            try:
                rsp_d = json.loads(to_string(rsp.body))
            except ValueError as e:
                raise TaskServerError(str(e))
            else:
                raise gen.Return(rsp_d)
