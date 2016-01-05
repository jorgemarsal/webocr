import logging
import os

# must be in caps

PORT = 1234
LOGGING_LEVEL = logging.DEBUG
LOGGING_FORMAT = '[%(asctime)s] p%(process)s {%(filename)s:' \
                 '%(lineno)d} %(levelname)s - %(message)s'

DB_HOSTNAME = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_NAME = 'webocr'

CELERY_API_ENDPOINT = 'http://localhost:8888'

TESSDATA_PREFIX = '/home/jorgem/Downloads/tesseract-ocr'
