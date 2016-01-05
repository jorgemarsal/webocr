#!/usr/bin/env python

import os
import sys
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES


PY2 = sys.version_info[0] == 2

cwd = os.path.dirname(os.path.abspath(__file__))

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(name='webocr',
      version='0.1.0',
      description='Web Optical Character Recognition',
      author='Jorge Martinez',
      author_email='jorge.marsal@gmail.com',
      url='https://github.com/jorgemarsal/webocr',
      packages=['webocr'],
      package_data={
          'webocr': ['conf/*', 'www/*',
                               'www/*/*',
                               'www/*/*/*']
      })
