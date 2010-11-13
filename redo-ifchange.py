#!/usr/bin/python
import sys, os
import vars
from helpers import sname, add_dep, debug, err, mkdirp, unlink


def _dirty_deps(t, depth):
    debug('%s?%s\n' % (depth, t))
    if not os.path.exists(sname('stamp', t)):
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return True

    stamptime = os.stat(sname('stamp', t)).st_mtime
    try:
        realtime = os.stat(t).st_mtime
    except OSError:
        realtime = 0

    if stamptime != realtime:
        debug('%s-- DIRTY (mtime)\n' % depth)
        return True
    
    for sub in open(sname('dep', t)).readlines():
        assert(sub[0] in ('c','m'))
        assert(sub[1] == ' ')
        assert(sub[-1] == '\n')
        mode = sub[0]
        name = sub[2:-1]
        if mode == 'c':
            if os.path.exists(name):
                debug('%s-- DIRTY (created)\n' % depth)
                return True
        elif mode == 'm':
            if dirty_deps(name, depth + '  '):
                #debug('%s-- DIRTY (sub)\n' % depth)
                return True
    return False


def dirty_deps(t, depth):
    if _dirty_deps(t, depth):
        unlink(sname('stamp', t))  # short circuit future checks
        return True
    return False


if not vars.TARGET:
    err('redo-ifchange: error: must be run from inside a .do\n')
    sys.exit(100)

try:
    want_build = []
    for t in sys.argv[1:]:
        mkdirp('%s/.redo' % vars.BASE)
        add_dep(vars.TARGET, 'm', t)
        if dirty_deps(t, depth = ''):
            want_build.append(t)

    if want_build:
        os.execvp('redo', ['redo', '--'] + want_build)
except KeyboardInterrupt:
    sys.exit(200)
