#!/bin/sh

export PYTHONPATH=$HOME/usr/opt/pyyaml/lib/python2.6/site-packages
python -c '
import sys, json, yaml
with open(sys.argv[1]) as f:
   print yaml.safe_dump(json.load(f), default_flow_style=False)
' $@
