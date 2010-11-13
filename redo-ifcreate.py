#!/usr/bin/python
import sys, os
import vars
from helpers import err, add_dep, mkdirp


if not vars.TARGET:
    err('redo-ifcreate: error: must be run from inside a .do\n')
    sys.exit(100)

try:
    for t in sys.argv[1:]:
        mkdirp('%s/.redo' % vars.BASE)
        if os.path.exists(t):
            err('redo-ifcreate: error: %r already exists\n' % t)
            sys.exit(1)
        else:
            add_dep(vars.TARGET, 'c', t)
except KeyboardInterrupt:
    sys.exit(200)
