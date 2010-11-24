#!/usr/bin/python
import sys, os, errno
import vars, state, builder, jwack
from helpers import debug, err, mkdirp, unlink


def dirty_deps(t, depth):
    try:
        st = os.stat(t)
        realtime = st.st_mtime
    except OSError:
        st = None
        realtime = 0
    
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


rv = 202
try:
    try:
        targets = sys.argv[1:]
        for t in targets:
            state.add_dep(vars.TARGET, 'm', t)
        rv = builder.main(targets, should_build)
    finally:
        jwack.force_return_tokens()
except KeyboardInterrupt:
    sys.exit(200)
sys.exit(rv)
