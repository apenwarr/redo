#!/usr/bin/env python
import sys, os

import vars_init
vars_init.init(sys.argv[1:])

import vars, state, builder, jwack, deps
from helpers import unlink
from log import debug, debug2, err

def should_build(t):
    f = state.File(name=t)
    if f.is_failed():
        raise builder.ImmediateReturn(32)
    dirty = deps.isdirty(f, depth = '', max_changed = vars.RUNID)
    return dirty==[f] and deps.DIRTY or dirty


rv = 202
try:
    if vars.TARGET and not vars.UNLOCKED:
        me = os.path.join(vars.STARTDIR, 
                          os.path.join(vars.PWD, vars.TARGET))
        f = state.File(name=me)
        debug2('TARGET: %r %r %r\n' % (vars.STARTDIR, vars.PWD, vars.TARGET))
    else:
        f = me = None
        debug2('redo-ifchange: not adding depends.\n')
    try:
        targets = sys.argv[1:]
        if f:
            for t in targets:
                f.add_dep('m', t)
            f.save()
        rv = builder.main(targets, should_build)
    finally:
        jwack.force_return_tokens()
except KeyboardInterrupt:
    sys.exit(200)
state.commit()
sys.exit(rv)
