import json
import logging
import os
import time

import pytest
import tornado
from tornado.httpclient import HTTPRequest, HTTPError
import websocket

from webocr._compat import to_string
from webocr.app import App
from webocr.config import Config
from webocr.db import SchemalessDb
from webocr.taskserver import CeleryRestTornadoTaskServer


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def app():
    c = Config('.')
    c.from_pyfile('{}/../webocr/conf/dev-conf.py'.format(
        os.path.abspath(os.path.dirname(__file__))))
    db = SchemalessDb(c)
    task_server = CeleryRestTornadoTaskServer(c)

    app = App(c, db, task_server)
    return app.app


@tornado.gen.coroutine
def service_ok(http_client, base_url, url):
    rsp = yield http_client.fetch('{}/api/v1/services'.format(base_url),
                                  method='POST',
                                  body=json.dumps({
                                      "url": url}))
    assert rsp.code == 202
    assert 'Content-Location' in rsp.headers

    while True:
        try:
            rsp2 = yield http_client.fetch(
                '{}{}'.format(
                    base_url,
                    rsp.headers['Content-Location']),
                method='GET',
                follow_redirects=False)
        except HTTPError as e:
            assert e.code == 303
            location = e.args[2].headers['Location']
            break
        else:
            assert rsp2.code == 200
            print(rsp2.body)
            time.sleep(0.2)
    assert location
    rsp3 = yield http_client.fetch('{}{}'.format(base_url, location),
                                   method='GET')
    assert rsp3.code == 200


@tornado.gen.coroutine
def service_fail(http_client, base_url, url):
    rsp = yield http_client.fetch('{}/api/v1/services'.format(base_url),
                                  method='POST',
                                  body=json.dumps({
                                      "url": url}))
    assert rsp.code == 202

    @tornado.gen.coroutine
    def poll():
        while True:
            rsp2 = yield http_client.fetch(
                '{}{}'.format(base_url, rsp. headers['Content-Location']),
                method='GET',
                follow_redirects=False)
            assert rsp2.code != 303
            state = json.loads(to_string(rsp2.body))['state']
            if state == 'FAILED':
                break
    yield poll()


@tornado.gen.coroutine
def bad_param(http_client, base_url, url=None, tag=None, ports=None):
    d = {}
    if url:
        d['url'] = url

    try:
        yield http_client.fetch('{}/api/v1/services'.format(base_url),
                                method='POST',
                                body=json.dumps(d))
    except HTTPError as e:
        assert e.code == 400


@pytest.mark.gen_test(timeout=10)
def test_create_service(http_client, base_url):
    yield service_ok(http_client, base_url,
                     url="{}/static/ocr/sample1.jpg".format(base_url))


@pytest.mark.gen_test
def test_bad_url(http_client, base_url):
    yield service_fail(http_client, base_url,
                       url="garbage")


@pytest.mark.gen_test
def test_get_index(http_client, base_url):
    rsp = yield http_client.fetch(base_url)
    assert rsp.code == 200


@pytest.mark.gen_test
def test_missing_url(http_client, base_url):
    yield bad_param(
        http_client, base_url
    )


@pytest.mark.gen_test
def test_queue_pending_task(app, http_client, base_url):
    task_id = 'my_task'
    task = dict(state='PENDING')
    app.service_manager.pending_tasks[task_id] = task
    rsp = yield http_client.fetch(base_url + '/queue/{}'.format(task_id))
    assert rsp.code == 200
    assert json.loads(to_string(rsp.body))['state'] == 'PENDING'


@pytest.mark.gen_test
def test_queue_successful_task(app, http_client, base_url):
    task_id = 'my_task'
    task = dict(state='RUNNING',
                service_id='1')
    app.service_manager.pending_tasks[task_id] = task
    req = HTTPRequest(url=base_url+'/queue/{}'.format(task_id),
                      follow_redirects=False)
    try:
        yield http_client.fetch(req)
    except HTTPError as e:
        assert e.args[2].code == 303
        assert e.args[2].headers['Location'] == \
            '/api/v1/service/{}'.format(task['service_id'])


@pytest.mark.gen_test
def test_queue_failed_task(app, http_client, base_url):
    task_id = 'my_task'
    task = dict(state='FAILED')
    app.service_manager.pending_tasks[task_id] = task
    rsp = yield http_client.fetch(base_url + '/queue/{}'.format(task_id))
    assert rsp.code == 200
    assert json.loads(to_string(rsp.body))['state'] == 'FAILED'


@pytest.mark.gen_test
def test_get_services(app, http_client, base_url):
    app.service_manager.db.execute("DELETE FROM entities; "
                                   "DELETE FROM index_url; "
                                   "DELETE FROM index_service_id;")
    app.service_manager.db.put(dict(
        url='url',
        state='PENDING'
    ))
    req = HTTPRequest(url=base_url+'/api/v1/services')
    rsp = yield http_client.fetch(req)
    assert rsp.code == 200
    assert json.loads(to_string(rsp.body)) == \
        {"services": [{"url": "url",
                       "state": "PENDING"}]}


@pytest.mark.gen_test
def test_get_existing_service(app, http_client, base_url):
    app.service_manager.db.execute("DELETE FROM entities; "
                                   "DELETE FROM index_url; "
                                   "DELETE FROM index_service_id;")
    row = app.service_manager.db.put(dict(
        url='url',
        state='PENDING'
    ))

    query = "select added_id from entities where HEX(id)='%s';" % (
        to_string(row['id']))
    added_id = app.service_manager.db.query(query)

    req = HTTPRequest(url=base_url+'/api/v1/service/{}'.format(
        added_id[0]['added_id']))
    rsp = yield http_client.fetch(req)
    assert rsp.code == 200
    assert json.loads(to_string(rsp.body)) == \
        {"state": "PENDING", "url": "url"}


@pytest.mark.gen_test
def test_get_missing_service(app, http_client, base_url):
    app.service_manager.db.execute("DELETE FROM entities; "
                                   "DELETE FROM index_url; "
                                   "DELETE FROM index_service_id;")
    req = HTTPRequest(url=base_url+'/api/v1/service/1234')
    try:
        yield http_client.fetch(req)
    except HTTPError as e:
        assert e.code == 404


@pytest.mark.gen_test
def test_websockets(base_url):
    ws = websocket.WebSocket()
    ws.connect('ws://localhost:1234/websocket')
    ws.close()
