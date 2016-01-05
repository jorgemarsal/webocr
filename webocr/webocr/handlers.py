import json
import re

import tornado.gen
import tornado.web
import tornado.websocket

from ._compat import to_string
from .service import ServiceError


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class QueueHandler(tornado.web.RequestHandler):
    def get(self, path=None):
        task_id = path.replace('/', '')
        try:
            task_info = self.application.service_manager.get_task_info(task_id)
        except KeyError:
            self.set_status(404)
            self.finish()
        else:
            if task_info['state'] != 'SUCCESS':
                self.write(task_info)
            else:
                self.set_status(303)
                assert 'service_id' in task_info
                self.redirect('/api/v1/service/{}'.format(
                    task_info['service_id']), status=303)


class ServiceResourceV1(tornado.web.RequestHandler):
    def get(self, path=None):
        if path == 'services' or path == 'services/':
            """Return all services
            We cannot return a list due to security risks,
            so we wrap it in an object"""
            self.write(
                {"services": self.application.service_manager.get_services()})
        else:
            """Return requested service"""
            try:
                service_id = re.findall(r'service/(\d+)', path)[0]
            except:
                self.set_status(404)
            else:
                try:
                    service = self.application.service_manager.get_service(
                        service_id)
                except KeyError:
                    self.set_status(404)
                    self.write('Service {} not found'.format(service_id))
                else:
                    self.write(service)

    @tornado.gen.coroutine
    def post(self, path=None):
        json_str = to_string(self.request.body)
        try:
            service = json.loads(json_str)
        except ValueError as e:
            self.set_status(400)
            self.write('{"msg":"%s"}' % (e))
        else:
            try:
                pending_task_id = \
                    yield self.application.service_manager.create(service)
            except ServiceError as e:
                self.set_status(400)
            else:
                self.set_status(202)
                self.set_header("Content-Location",
                                "/queue/{}".format(pending_task_id))


class StatusHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.application.service_manager.register(self.callback)

    def on_close(self):
        self.application.service_manager.unregister(self.callback)

    def on_message(self, message):
        pass

    def callback(self, message):
        self.write_message(message)
