#!/usr/bin/python
import sys, os, errno
import vars, state, builder
from helpers import debug, err, mkdirp, unlink


def dirty_deps(t, depth):
    debug('%s?%s\n' % (depth, t))
    if state.isbuilt(t):
        debug('%s-- DIRTY (built)\n' % depth)
        return True  # has already been built during this session
    if state.ismarked(t):
        debug('%s-- CLEAN (marked)\n' % depth)
        return False  # has already been checked during this session
    
    stamptime = state.stamped(t)
    if stamptime == None:
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return True

    try:
        realtime = os.stat(t).st_mtime
    except OSError:
        realtime = 0

    if stamptime != realtime:
        debug('%s-- DIRTY (mtime)\n' % depth)
        return True
    
    for mode,name in state.deps(t):
        if mode == 'c':
            if os.path.exists(name):
                debug('%s-- DIRTY (created)\n' % depth)
                return True
        elif mode == 'm':
            if dirty_deps(os.path.join(vars.BASE, name), depth + '  '):
                debug('%s-- DIRTY (sub)\n' % depth)
                state.unstamp(t)  # optimization for future callers
                return True
    state.mark(t)
    return False


def should_build(t):
    return not state.isbuilt(t) and dirty_deps(t, depth = '')


def maybe_build(t):
    if should_build(t):
        builder.build(t)


if not vars.TARGET:
    err('redo-ifchange: error: must be run from inside a .do\n')
    sys.exit(100)

rv = 202
try:
    want_build = []
    for t in sys.argv[1:]:
        state.add_dep(vars.TARGET, 'm', t)
        if should_build(t):
            want_build.append(t)

    rv = builder.main(want_build, maybe_build)
except KeyboardInterrupt:
    sys.exit(200)
sys.exit(rv)
