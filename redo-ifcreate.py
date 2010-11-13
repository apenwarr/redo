#!/usr/bin/python
import sys, os
import vars
from helpers import *


if not vars.TARGET:
    sys.stderr.write('redo-ifcreate: error: must be run from inside a .do\n')
    sys.exit(1)

for t in sys.argv[1:]:
    mkdirp('%s/.redo' % vars.BASE)
    if os.path.exists(t):
        add_dep(vars.TARGET, 'm', t)
    else:
        add_dep(vars.TARGET, 'c', t)
