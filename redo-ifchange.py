#!/usr/bin/env python
import sys, os

import vars_init
vars_init.init(sys.argv[1:])

import vars, state, builder, deps
from log import debug, debug2, err


def should_build(t):
    f = state.File(t)
    if f.stamp_mtime >= vars.RUNID and f.exitcode:
        raise Exception('earlier build of %r failed with code %d'
                        % (f.name, f.exitcode))
    if f.stamp_mtime == 0:
        expect_stamp = None
    else:
        expect_stamp = f.csum or f.stamp
    dirty = deps.isdirty(f, depth='', expect_stamp=expect_stamp,
                         max_runid=vars.RUNID)
    return dirty==[f] and deps.DIRTY or dirty


def build_ifchanged(sf):
    dirty = should_build(sf.name)
    if dirty and dirty != deps.DIRTY:
        # FIXME: bring back the old (targetname) notation in the output
        #  when we need to do this.  And add comments.
        for t2 in dirty:
            rv = build_ifchanged(t2)
            if rv:
                return rv
        dirty = should_build(sf.name)
        #assert(dirty in (deps.DIRTY, deps.CLEAN))
    if dirty:
        rv = builder.build(sf.name)
        if rv:
            return rv
    return 0


retcode = 202
any_errors = 0
try:
    targets = sys.argv[1:]
    targets = state.fix_chdir(targets)
    if vars.TARGET:
        f = state.File(name=vars.TARGET)
        debug2('TARGET: %r %r %r\n', vars.STARTDIR, vars.PWD, vars.TARGET)
    else:
        f = me = None
        debug2('redo-ifchange: no target - not adding depends.\n')

    retcode = 0
    for t in targets:
        sf = state.File(name=t)
        retcode = build_ifchanged(sf)
        any_errors += retcode
        if f:
            sf.refresh()
            f.add_dep(sf)
        if retcode and not vars.KEEP_GOING:
            sys.exit(retcode)
except KeyboardInterrupt:
    sys.exit(200)
if any_errors:
    sys.exit(1)
