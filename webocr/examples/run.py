import os

from webocr.app import App
from webocr.config import Config
from webocr.db import SchemalessDb
from webocr.taskserver import CeleryRestTornadoTaskServer


if __name__ == '__main__':
    c = Config('.')
    c.from_pyfile('{}/../webocr/conf/dev-conf.py'.format(
        os.path.abspath(os.path.dirname(__file__))))
    db = SchemalessDb(c)
    task_server = CeleryRestTornadoTaskServer(c)

    app = App(c, db, task_server)
    app.run()
