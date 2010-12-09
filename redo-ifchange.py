#!/usr/bin/python
import sys, os, errno, stat
import vars, state, builder, jwack
from helpers import debug, debug2, err, unlink


def dirty_deps(f, depth, max_changed):
    if vars.DEBUG >= 1: debug('%s?%s\n' % (depth, f.name))

    if f.changed_runid == None:
        debug('%s-- DIRTY (never built)\n' % depth)
        return True
    if f.changed_runid > max_changed:
        debug('%s-- DIRTY (built)\n' % depth)
        return True  # has been built more recently than parent
    if f.is_checked():
        if vars.DEBUG >= 1: debug('%s-- CLEAN (checked)\n' % depth)
        return False  # has already been checked during this session

    if not f.stamp:
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return True

    if f.stamp != f.read_stamp():
        debug('%s-- DIRTY (mtime)\n' % depth)
        return True
    
    for mode,f2 in f.deps():
        if mode == 'c':
            if os.path.exists(os.path.join(vars.BASE, f2.name)):
                debug('%s-- DIRTY (created)\n' % depth)
                return True
        elif mode == 'm':
            if dirty_deps(f2, depth = depth + '  ',
                          max_changed = f.changed_runid):
                debug('%s-- DIRTY (sub)\n' % depth)
                return True
    f.set_checked()
    f.save()
    return False


def should_build(t):
    f = state.File(name=t)
    return dirty_deps(f, depth = '', max_changed = vars.RUNID)


rv = 202
try:
    me = os.path.join(vars.STARTDIR, 
                      os.path.join(vars.PWD, vars.TARGET))
    f = state.File(name=me)
    debug2('TARGET: %r %r %r\n' % (vars.STARTDIR, vars.PWD, vars.TARGET))
    try:
        targets = sys.argv[1:]
        for t in targets:
            f.add_dep('m', t)
        f.save()
        rv = builder.main(targets, should_build)
    finally:
        jwack.force_return_tokens()
except KeyboardInterrupt:
    sys.exit(200)
sys.exit(rv)
