#!/usr/bin/env python
import sys, os
import vars, state
from log import err


try:
    targets = sys.argv[1:]
    targets = state.fix_chdir(targets)
    f = state.File(vars.TARGET)
    for t in targets:
        if os.path.exists(t):
            err('redo-ifcreate: error: %r already exists\n' % t)
            sys.exit(1)
        else:
            f.add_dep(state.File(name=t))
except KeyboardInterrupt:
    sys.exit(200)
