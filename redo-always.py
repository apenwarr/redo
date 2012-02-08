#!/usr/bin/env python
import sys, os
import vars, state
from log import err


try:
    state.fix_chdir([])
    f = state.File(name=vars.TARGET)
    f.add_dep(state.File(name=state.ALWAYS))
except KeyboardInterrupt:
    sys.exit(200)
