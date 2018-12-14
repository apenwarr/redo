"""Manage redo-related environment variables."""
import os, sys
from .atoi import atoi

is_toplevel = False

v = None


def _get(name, default):
    return os.environ.get(name, default)


def _get_int(name, default):
    return atoi(_get(name, str(default)))


def _get_bool(name, default):
    return 1 if _get(name, default) else 0


class Env(object):
    def __init__(self):
        # Mandatory.  If this is missing, you forgot to call init().
        self.BASE = os.environ['REDO_BASE'].rstrip('/')

        # Everything else, we can recover from defaults if unset.
        self.PWD = _get('REDO_PWD', '')
        self.TARGET = _get('REDO_TARGET', '')
        self.DEPTH = _get('REDO_DEPTH', '')
        self.DEBUG = atoi(_get('REDO_DEBUG', ''))
        self.DEBUG_LOCKS = _get_bool('REDO_DEBUG_LOCKS', '')
        self.DEBUG_PIDS = _get_bool('REDO_DEBUG_PIDS', '')
        self.VERBOSE = _get_bool('REDO_VERBOSE', '')
        self.XTRACE = _get_bool('REDO_XTRACE', '')
        self.KEEP_GOING = _get_bool('REDO_KEEP_GOING', '')
        self.LOG = _get_int('REDO_LOG', 1)  # defaults on
        self.LOG_INODE = _get('REDO_LOG_INODE', '')
        self.COLOR = _get_int('REDO_COLOR', 1)  # defaults on
        # subprocesses mustn't pretty-print if a parent is running redo-log
        self.PRETTY = (not self.LOG) and _get_int('REDO_PRETTY', 1)
        self.SHUFFLE = _get_bool('REDO_SHUFFLE', '')
        self.STARTDIR = _get('REDO_STARTDIR', '')
        self.RUNID = _get_int('REDO_RUNID', '') or None
        self.UNLOCKED = _get_bool('REDO_UNLOCKED', '')
        self.NO_OOB = _get_bool('REDO_NO_OOB', '')


def inherit():
    """Read environment (which must already be set) to get runtime settings."""

    if not os.environ.get('REDO'):
        sys.stderr.write('%s: error: must be run from inside a .do\n'
                         % sys.argv[0])
        sys.exit(100)

    global v
    v = Env()

    # not inheritable by subprocesses
    os.environ['REDO_UNLOCKED'] = ''
    os.environ['REDO_NO_OOB'] = ''


def init_no_state():
    """Start a session (if needed) for a command that needs no state db."""
    global is_toplevel
    if not os.environ.get('REDO'):
        os.environ['REDO'] = 'NOT_DEFINED'
        is_toplevel = True
    if not os.environ.get('REDO_BASE'):
        os.environ['REDO_BASE'] = 'NOT_DEFINED'
    inherit()


def init(targets):
    """Start a session (if needed) for a command that does need the state db.

    Args:
      targets: a list of targets we're trying to build.  We use this to
        help in guessing where the .redo database is located.
    """
    global is_toplevel
    if not os.environ.get('REDO'):
        # toplevel call to redo
        is_toplevel = True
        exenames = [os.path.abspath(sys.argv[0]),
                    os.path.realpath(sys.argv[0])]
        dirnames = [os.path.dirname(p) for p in exenames]
        trynames = ([os.path.abspath(p+'/../lib/redo') for p in dirnames] +
                    [p+'/../redo' for p in dirnames] +
                    dirnames)
        seen = {}
        dirs = []
        for k in trynames:
            if not seen.get(k):
                seen[k] = 1
                dirs.append(k)
        os.environ['PATH'] = ':'.join(dirs) + ':' + os.environ['PATH']
        os.environ['REDO'] = os.path.abspath(sys.argv[0])

    if not os.environ.get('REDO_BASE'):
        if not targets:
            # if no other targets given, assume the current directory
            targets = ['all']
        base = os.path.commonprefix([os.path.abspath(os.path.dirname(t))
                                     for t in targets] + [os.getcwd()])
        bsplit = base.split('/')
        for i in range(len(bsplit)-1, 0, -1):
            newbase = '/'.join(bsplit[:i])
            if os.path.exists(newbase + '/.redo'):
                base = newbase
                break
        os.environ['REDO_BASE'] = base
        os.environ['REDO_STARTDIR'] = os.getcwd()

    inherit()
