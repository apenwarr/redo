#!/usr/bin/python
import sys, os, errno
import vars
from helpers import sname, add_dep, debug, err, mkdirp, unlink


def _dirty_deps(t, depth, fromdir):
    debug('%s?%s\n' % (depth, t))
    try:
        stamptime = os.stat(sname('stamp', t, fromdir)).st_mtime
    except OSError, e:
        if e.errno == errno.ENOENT:
            debug('%s-- DIRTY (no stamp)\n' % depth)
            return True
        else:
            raise

    try:
        realtime = os.stat(os.path.join(fromdir or '', t)).st_mtime
    except OSError:
        realtime = 0

    if stamptime != realtime:
        debug('%s-- DIRTY (mtime)\n' % depth)
        return True
    
    for sub in open(sname('dep', t, fromdir)).readlines():
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
            if dirty_deps(name, depth + '  ', fromdir=vars.BASE):
                #debug('%s-- DIRTY (sub)\n' % depth)
                return True
    return False


def dirty_deps(t, depth, fromdir=None):
    if _dirty_deps(t, depth, fromdir):
        unlink(sname('stamp', t, fromdir))  # short circuit future checks
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
