#!/usr/bin/env python
import sys

import vars_init
vars_init.init([])

import state
for n in sys.argv[1:]:
    f = state.File(name=n)
    f.set_static()
    f.save()
state.commit()
