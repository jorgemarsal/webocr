#!/bin/sh

python -c 'import sys, yaml, json;json.dump(yaml.load(open(sys.argv[1]).read()), sys.stdout, indent=4)' $@
