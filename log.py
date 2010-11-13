import sys, os
import vars


def _log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()


def _clog(s):
    _log('\x1b[32mredo: %s\x1b[1m%s\x1b[m' % (vars.DEPTH, s))
def _bwlog(s):
    _log('redo: %s%s' % (vars.DEPTH, s))
if os.isatty(2):
    log = _clog
else:
    log = _bwlog


def debug(s):
    if vars.DEBUG:
        _log('redo: %s%s' % (vars.DEPTH, s))
