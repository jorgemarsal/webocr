from concurrent.futures import ThreadPoolExecutor
import logging
import os

import tornado.ioloop
import tornado.web

from .handlers import \
    ServiceResourceV1, MainHandler, StatusHandler, QueueHandler
from .service import ServiceManager


class App(object):
    def __init__(self, config, db, task_server):
        logging.basicConfig(format=config.get('LOGGING_FORMAT'),
                            level=config.get('LOGGING_LEVEL'))

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "www"),
            static_path=os.path.join(os.path.dirname(__file__), "www"),
        )
        self.app = tornado.web.Application(
            handlers=[
                (r"/", MainHandler),
                (r"/queue/(.*)", QueueHandler),
                (r"/websocket", StatusHandler),
                (r"/api/v1/(.*)", ServiceResourceV1)
            ],
            **settings
        )

        self.app.executor = ThreadPoolExecutor(max_workers=4)
        self.app.service_manager = ServiceManager(config,
                                                  self.app,
                                                  db,
                                                  task_server)

        self.app.config = config
        level = self.app.config.get('LOGGING_LEVEL', logging.WARNING)
        logging.basicConfig(level=level,
                            format='%(asctime)s %(name)-12s '
                                   '%(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',)

    def run(self):
        port = self.app.config.get('PORT', 1234)

        logging.info('Listening on http://*:%d' % port)
        self.app.listen(port)
        tornado.ioloop.IOLoop.instance().start()
