#!/usr/bin/env python2
import sys, os

import vars_init
vars_init.init([])

import vars, state, deps
from logs import err

if len(sys.argv[1:]) != 0:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)


cache = {}

def is_checked(f):
    return cache.get(f.id, 0)

def set_checked(f):
    cache[f.id] = 1


cwd = os.getcwd()
for f in state.files():
    if f.is_generated and f.read_stamp() != state.STAMP_MISSING:
        if deps.isdirty(f, depth='', max_changed=vars.RUNID,
                        already_checked=[],
                        is_checked=is_checked, set_checked=set_checked):
            print state.relpath(os.path.join(vars.BASE, f.name), cwd)
