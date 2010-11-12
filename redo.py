#!/usr/bin/python
import sys, os, subprocess
import options
from helpers import *

optspec = """
redo [targets...]
--
d,debug    print dependency checks as they happen
ifchange   only redo if the file is modified or deleted
ifcreate   only redo if the file is created
"""
o = options.Options('redo', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra or ['it']


def log(s):
    sys.stdout.flush()
    sys.stderr.write('redo: %s%s' % (REDO_DEPTH, s))
    sys.stderr.flush()


def debug(s):
    if REDO_DEBUG:
        log(s)


def add_dep(t, mode, dep):
    open('.redo/dep.%s' % t, 'a').write('%s %s\n' % (mode, dep))
    

def find_do_file(t):
    dofile = '%s.do' % t
    if os.path.exists(dofile):
        add_dep(t, 'm', dofile)
        if dirty_deps(dofile, depth = ''):
            build(dofile)
        return dofile
    else:
        add_dep(t, 'c', dofile)
        return None


def _dirty_deps(t, depth):
    debug('%s?%s\n' % (depth, t))
    if not os.path.exists('.redo/stamp.%s' % t):
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return True

    stamptime = os.stat('.redo/stamp.%s' % t).st_mtime
    try:
        realtime = os.stat(t).st_mtime
    except OSError:
        realtime = 0

    if stamptime != realtime:
        debug('%s-- DIRTY (mtime)\n' % depth)
        return True
    
    for sub in open('.redo/dep.%s' % t).readlines():
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
        unlink('.redo/stamp.%s' % t)  # short circuit future checks
        return True
    return False


def stamp(t):
    stampfile = '.redo/stamp.%s' % t
    open(stampfile, 'w').close()
    try:
        mtime = os.stat(t).st_mtime
    except OSError:
        mtime = 0
    os.utime(stampfile, (mtime, mtime))


def build(t):
    unlink('.redo/dep.%s' % t)
    open('.redo/dep.%s' % t, 'w').close()
    dofile = find_do_file(t)
    if not dofile:
        if os.path.exists(t):  # an existing source file
            stamp(t)
            return  # success
        else:
            raise Exception('no rule to make %r' % t)
    unlink(t)
    os.putenv('REDO_TARGET', t)
    os.putenv('REDO_DEPTH', REDO_DEPTH + '  ')
    tmpname = '%s.redo.tmp' % t
    unlink(tmpname)
    f = open(tmpname, 'w+')
    argv = ['sh', '-e', dofile, t, 'FIXME', tmpname]
    log('%s\n' % t)
    rv = subprocess.call(argv, stdout=f.fileno())
    st = os.stat(tmpname)
    #log('rv: %d (%d bytes) (%r)\n' % (rv, st.st_size, dofile))
    stampfile = '.redo/stamp.%s' % t
    if rv==0:
        if st.st_size:
            os.rename(tmpname, t)
        else:
            unlink(tmpname)
        stamp(t)
    else:
        unlink(tmpname)
        unlink(stampfile)
    f.close()
    if rv != 0:
        raise Exception('non-zero return code building %r' % t)


mkdirp('.redo')
REDO_TARGET = os.getenv('REDO_TARGET', '')
REDO_DEPTH = os.getenv('REDO_DEPTH', '')

assert(not (opt.ifchange and opt.ifcreate))
if opt.debug:
    REDO_DEBUG = 1
    os.putenv('REDO_DEBUG', '1')
else:
    REDO_DEBUG = os.getenv('REDO_DEBUG', '') and 1 or 0

for t in targets:
    if REDO_TARGET:
        add_dep(REDO_TARGET, opt.ifcreate and 'c' or 'm', t)
    if opt.ifcreate:
        pass # just adding the dependency (above) is enough
    elif opt.ifchange:
        if dirty_deps(t, depth = ''):
            build(t)
    else:
        build(t)
