#!/usr/bin/python
import sys, os
import vars, state
from helpers import err


try:
    me = state.File(name=vars.TARGET)
    me.add_dep('m', state.ALWAYS)
    always = state.File(name=state.ALWAYS)
    always.stamp = state.STAMP_MISSING
    always.set_changed()
    always.save()
    state.commit()
except KeyboardInterrupt:
    sys.exit(200)
