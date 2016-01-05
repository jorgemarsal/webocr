import logging

import schemaless
from tornado import ioloop, gen
from tornado.concurrent import run_on_executor

from .taskserver import TaskServerError
from ._compat import to_string


class ServiceError(Exception):
    pass


class ServiceManager(object):
    def __init__(self, config, tornado_app, db, task_server):
        self.config = config
        self.tornado_app = tornado_app
        self.db = db
        self.task_server = task_server

        self.executor = self.tornado_app.executor
        """Function to send messages to a Websocket connection"""
        self.ws_send_fn = None
        """Bookkeeping of the tasks sent to Celery"""
        self.pending_tasks = {}

    @run_on_executor
    def _on_executor(self, fn, *args, **kwargs):
        """Execute the given function on another thread"""
        return fn(*args, **kwargs)

    @gen.coroutine
    def _wait_for_task_completed(self, ctx, timeout=3600, wait_time=0.2,
                                 on_success=None, on_fail=None,
                                 on_revoked=None):
        """Poll the task service until the task is completed"""
        loop = ioloop.IOLoop.current()
        tic = loop.time()

        while loop.time() - tic < timeout:
            """If another exception type is raised it's not handled in th
            caller, because this function runs in a `spawn_callback` call.
            The exceptions are logged."""
            try:
                rsp = yield self.task_server.get_status(ctx['task_id'])
            except TaskServerError as e:
                yield self._on_fail(
                    ctx,
                    'Unable to connect to task server: {}'.format(str(e)))
                raise gen.Return()
            else:
                task_id = rsp['task-id']
                state = rsp['state'].upper()
                self.pending_tasks[task_id]['celery_state'] = rsp
                if state == 'PENDING' or \
                            state == 'RECEIVED' or \
                            state == 'STARTED' or \
                            state == 'RETRY':
                    yield gen.Task(loop.add_timeout,
                                   loop.time() + wait_time)
                else:
                    if state == 'SUCCESS':
                        ctx['result'] = rsp['result']
                        yield self._on_success(ctx)
                    elif state == 'FAILURE':
                        yield self._on_fail(ctx, rsp.get('error'))
                    else:
                        yield self._on_fail(
                            ctx, 'Unknown taskserver state {}'.format(state))
                    raise gen.Return()
        raise RuntimeError('Timeout waiting for task {} to complete'.format(
            ctx['task_id']))

    @gen.coroutine
    def _on_success(self, ctx, msg=None):
        task_id = ctx['task_id']
        logging.debug('task {} succeeded'.format(task_id))

        # add entry to db
        updated_row = ctx['db_row'].copy()
        updated_row['state'] = 'SUCCESS'
        updated_row['result'] = ctx['result']
        self.db.put(updated_row)
        """Important to set state to SUCCESS after updating the database.
        Otherwise a client may try to fetch the service info and get a 404"""
        self.pending_tasks[ctx['task_id']]['state'] = 'SUCCESS'

        """Send debug info to the WS channel"""
        if self.ws_send_fn is not None:
            self.ws_send_fn('Done!')

    @gen.coroutine
    def _on_fail(self, ctx, error=None):
        task_id = ctx['task_id']
        logging.debug('task {} fail'.format(task_id))
        self.pending_tasks[task_id]['state'] = 'FAILED'
        if error:
            self.pending_tasks[task_id]['error'] = error
        # add entry to db
        updated_row = ctx['db_row'].copy()
        updated_row['state'] = 'FAILED'
        if error:
            updated_row['error'] = error
        self.db.put(updated_row)
        """Important to set state to running after updating the database.
        Otherwise a client may try to fetch the service info and get a 404"""
        self.pending_tasks[task_id]['state'] = 'FAILED'
        if self.ws_send_fn is not None:
            self.ws_send_fn('Deploy failed!')

    @gen.coroutine
    def _on_revoked(self, ctx, error=None):
        yield self._on_fail(ctx, "on_revoked is not implemented")

    @gen.coroutine
    def create(self, service):
        """Create a new service.

        :param service: dictionary containing the service configuration.
                        Required keys are `url` `tag` and `ports`.
                        `tag` must have the format`name:version`.
        :return:code 202 on success or raises an exception on failure.
        """
        def check_param(name):
            if name not in service:
                raise ServiceError(
                    "Missing required parameter {}".format(name))
        check_param('url')

        try:
            rsp = yield self.task_server.create(service, self.config)
        except TaskServerError as e:
            raise ServiceError(str(e))
        else:
            """Initialize task bookkeeping info"""
            self.pending_tasks[rsp['task-id']] = {
                "celery_state": rsp,
                "service": service,
                "state": 'PENDING'
            }
            """Create a new entry and get the `added_id` field which will be
            used as the `service_id`. `added_id` in an AUTO_INCREMENT field in
            the DB"""
            row = self.db.put(dict(
                url=service['url'],
                state='PENDING'
            ))

            query = "select added_id from entities where HEX(id)='%s';" % (
                to_string(row['id']))
            added_id = self.db.query(query)
            assert len(added_id) == 1
            assert 'added_id' in added_id[0]
            self.pending_tasks[rsp['task-id']]['service_id'] = \
                added_id[0]['added_id']

            current_ioloop = ioloop.IOLoop.current()
            """Fire-n-forget a task to poll for service status"""
            current_ioloop.spawn_callback(self._wait_for_task_completed,
                                          ctx=dict(task_id=rsp['task-id'],
                                                   db_row=row),
                                          on_success=self._on_success,
                                          on_fail=self._on_fail,
                                          on_revoked=self._on_revoked)
            """Return immediately to the client. For this point on the client
            can poll the status using the /queue endpoint"""
            raise gen.Return(rsp['task-id'])

    def register(self, callback):
        """Register the WS callback"""
        self.ws_send_fn = callback

    def unregister(self, callback):
        """Unregister the WS callback"""
        pass

    def get_task_info(self, task_id):
        """Used by the /queue endpoint to get task info"""
        return self.pending_tasks[task_id]

    def _get_service_helper(self, id=None):
        def clean_json(s):
            """Remove the `id` and `updated` fields because they aren't JSON
            serializable"""
            s.pop('id', None)
            s.pop('updated', None)
            return s

        query = "SELECT body FROM entities"
        if id:
            query += " WHERE added_id='{}'".format(id)
        query += ';'
        rows = self.db.query(query)
        services = []
        for r in rows:
            service = schemaless.Entity.from_row(r, use_zlib=True)
            clean_json(service)
            services.append(service)
        return services

    def get_services(self):
        """Get all the services"""
        return self._get_service_helper()

    def get_service(self, id):
        """Get a service by id"""
        services = self._get_service_helper(id)
        if not services:
            raise KeyError("Service {} not found".format(id))
        return services[0]
