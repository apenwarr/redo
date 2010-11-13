import sys, os, errno
import vars


def atoi(v):
    try:
        return int(v or 0)
    except ValueError:
        return 0


def unlink(f):
    """Delete a file at path 'f' if it currently exists.

    Unlike os.unlink(), does not throw an exception if the file didn't already
    exist.
    """
    try:
        os.unlink(f)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass  # it doesn't exist, that's what you asked for


def mkdirp(d, mode=None):
    """Recursively create directories on path 'd'.

    Unlike os.makedirs(), it doesn't raise an exception if the last element of
    the path already exists.
    """
    try:
        if mode:
            os.makedirs(d, mode)
        else:
            os.makedirs(d)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def _log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()


def _clog(s):
    _log('\x1b[32mredo: %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwlog(s):
    _log('redo: %s%s' % (vars.DEPTH, s))

def _cerr(s):
    _log('\x1b[31mredo: %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwerr(s):
    _log('redo: %s%s' % (vars.DEPTH, s))


if os.isatty(2):
    log = _clog
    err = _cerr
else:
    log = _bwlog
    err = _bwerr


def debug(s):
    if vars.DEBUG:
        _log('redo: %s%s' % (vars.DEPTH, s))


def relpath(t, base):
    t = os.path.abspath(t)
    tparts = t.split('/')
    bparts = base.split('/')
    for tp,bp in zip(tparts,bparts):
        if tp != bp:
            break
        tparts.pop(0)
        bparts.pop(0)
    while bparts:
        tparts.insert(0, '..')
        bparts.pop(0)
    return '/'.join(tparts)


def sname(typ, t):
    # FIXME: t.replace(...) is non-reversible and non-unique here!
    tnew = relpath(t, vars.BASE)
    #log('sname: (%r) %r -> %r\n' % (vars.BASE, t, tnew))
    return vars.BASE + ('/.redo/%s^%s' % (typ, tnew.replace('/', '^')))


def add_dep(t, mode, dep):
    open(sname('dep', t), 'a').write('%s %s\n' % (mode, dep))
