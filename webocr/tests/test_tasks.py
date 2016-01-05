import os

from webocr.config import Config
from webocr.tasks import create_service


def helper(url):
    service = dict(url=url)
    c = Config('.')
    c.from_pyfile('{}/../webocr/conf/dev-conf.py'.format(
        os.path.abspath(os.path.dirname(__file__))))

    return create_service.apply(args=[service, c])


def test_good_url():
    os.environ['TESSDATA_PREFIX'] = '/home/jorgem/Downloads/tesseract-ocr'
    res = helper('http://localhost:1234/static/ocr/sample1.jpg')
    assert res.state == 'SUCCESS'


def test_bad_url():
    res = helper('http://localhost:1234/static/ocr/idontexist')
    assert res.state == 'FAILURE'
