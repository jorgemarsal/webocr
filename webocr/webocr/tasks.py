import logging
import os
import tempfile
import uuid

from celery import Celery
import magic

from webocr._compat import to_string
from webocr.util import run_cmd, CmdException

celery = Celery("tasks",
                broker="amqp://guest@{}//".format(
                    os.environ.get('RABBITMQ_HOSTNAME', 'localhost')))
celery.conf.CELERY_RESULT_BACKEND = \
    os.environ.get('CELERY_RESULT_BACKEND', 'amqp')


@celery.task(name='webocr.create_service')
def create_service(service, config):
    logging.debug('service: {} config: {}'.format(service, config))

    # sanity checks
    def check_field_present(field):
        if field not in service:
            raise ValueError("Request doesn't have the {} field".format(field))

    check_field_present('url')
    logging.debug('Adding service: {}'.format(service))
    tmpdir = tempfile.mkdtemp()

    def run_helper(cmd, env=None):
        try:
            logging.debug('Running cmd: {}'.format(cmd))
            return run_cmd(cmd,
                           env=env,
                           stdout_callback=None,
                           stderr_callback=None)
        except CmdException:
            raise

    # download file
    run_helper('cd {}; curl -O {}'.format(tmpdir, service['url']))

    filename = tmpdir + '/' + service['url'].split('/')[-1]
    filetype = magic.from_file(filename)
    filebase = filename.split('.')[-1]

    clean_filetype = to_string(filetype).lower()
    if 'pdf' in clean_filetype:
        run_helper('cd {}; convert {} {}'.format(tmpdir,
                                                 filename,
                                                 filebase + '.png'))
        filename = filebase + '.png'
    elif 'jpeg' in clean_filetype or 'png' in clean_filetype:
        pass
    else:
        raise ValueError('File {} unsupported'.format(filename))

    # run tesseract
    output = tmpdir + '/' + str(uuid.uuid4())
    tesseract_cmd = \
        'cd {}; tesseract {} {}'.format(tmpdir, filename, output)
    run_helper('cd {}; {}'.format(tmpdir, tesseract_cmd))

    # return recognized text
    return open(output + '.txt').read()
