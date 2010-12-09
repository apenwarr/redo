#!/usr/bin/python
import sys, os
import vars, state
from helpers import err


try:
    me = state.File(name=vars.TARGET)
    for t in sys.argv[1:]:
        if os.path.exists(t):
            err('redo-ifcreate: error: %r already exists\n' % t)
            sys.exit(1)
        else:
            me.add_dep('c', t)
except KeyboardInterrupt:
    sys.exit(200)
