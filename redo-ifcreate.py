#!/usr/bin/env python
import sys, os
import vars, state
from log import err


try:
    me = os.path.join(vars.STARTDIR, 
                      os.path.join(vars.PWD, vars.TARGET))
    f = state.File(name=me)
    for t in sys.argv[1:]:
        if os.path.exists(t):
            err('redo-ifcreate: error: %r already exists\n' % t)
            sys.exit(1)
        else:
            f.add_dep('c', t)
    state.commit()
except KeyboardInterrupt:
    sys.exit(200)
