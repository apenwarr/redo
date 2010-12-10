import sys, os, errno, fcntl
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


def log_(s):
    sys.stdout.flush()
    if vars.DEBUG_PIDS:
        sys.stderr.write('%d %s' % (os.getpid(), s))
    else:
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

def _cwarn(s):
    log_('\x1b[33mredo: %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwwarn(s):
    log_('redo: %s%s' % (vars.DEPTH, s))


if os.isatty(2):
    log = _clog
    err = _cerr
    warn = _cwarn
else:
    log = _bwlog
    err = _bwerr
    warn = _bwwarn


def debug(s):
    if vars.DEBUG >= 1:
        log_('redo: %s%s' % (vars.DEPTH, s))
def debug2(s):
    if vars.DEBUG >= 2:
        log_('redo: %s%s' % (vars.DEPTH, s))
def debug3(s):
    if vars.DEBUG >= 3:
        log_('redo: %s%s' % (vars.DEPTH, s))


def close_on_exec(fd, yes):
    fl = fcntl.fcntl(fd, fcntl.F_GETFD)
    fl &= ~fcntl.FD_CLOEXEC
    if yes:
        fl |= fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, fl)


