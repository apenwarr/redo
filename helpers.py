import sys, os, errno
import vars


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


def log_(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()


def _clog(s):
    log_('\x1b[32mredo  %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwlog(s):
    log_('redo  %s%s' % (vars.DEPTH, s))

def _cerr(s):
    log_('\x1b[31mredo: %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwerr(s):
    log_('redo: %s%s' % (vars.DEPTH, s))


if os.isatty(2):
    log = _clog
    err = _cerr
else:
    log = _bwlog
    err = _bwerr


def debug(s):
    if vars.DEBUG >= 1:
        log_('redo: %s%s' % (vars.DEPTH, s))
def debug2(s):
    if vars.DEBUG >= 2:
        log_('redo: %s%s' % (vars.DEPTH, s))


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


def sname(typ, t, fromdir=None):
    # FIXME: t.replace(...) is non-reversible and non-unique here!
    if fromdir:
        t = os.path.join(fromdir, t)
    tnew = relpath(t, vars.BASE)
    v = vars.BASE + ('/.redo/%s^%s' % (typ, tnew.replace('/', '^')))
    debug2('sname: (%r) %r -> %r\n' % (os.getcwd(), t, tnew))
    return v


def add_dep(t, mode, dep):
    debug2('add-dep(%r)\n' % t)
    open(sname('dep', t), 'a').write('%s %s\n'
                                     % (mode, relpath(dep, vars.BASE)))
