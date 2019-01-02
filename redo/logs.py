"""Code for writing log-formatted messages to stderr."""
import os, re, sys, time
from . import env

RED = GREEN = YELLOW = BOLD = PLAIN = None


def _check_tty(tty, color):
    global RED, GREEN, YELLOW, BOLD, PLAIN
    color_ok = tty.isatty() and (os.environ.get('TERM') or 'dumb') != 'dumb'
    if (color and color_ok) or color >= 2:
        # ...use ANSI formatting codes.
        # pylint: disable=bad-whitespace
        RED    = "\x1b[31m"
        GREEN  = "\x1b[32m"
        YELLOW = "\x1b[33m"
        BOLD   = "\x1b[1m"
        PLAIN  = "\x1b[m"
    else:
        RED    = ""
        GREEN  = ""
        YELLOW = ""
        BOLD   = ""
        PLAIN  = ""


class RawLog(object):
    """A log printer for machine-readable logs, suitable for redo-log."""

    def __init__(self, tty):
        self.file = tty

    def write(self, s):
        assert '\n' not in s
        sys.stdout.flush()
        sys.stderr.flush()
        self.file.write(s + '\n')
        self.file.flush()


REDO_RE = re.compile(r'@@REDO:([^@]+)@@ (.*)$')


class PrettyLog(object):
    """A log printer for human-readable logs."""

    def __init__(self, tty):
        self.topdir = os.getcwd()
        self.file = tty

    def _pretty(self, pid, color, s):
        if env.v.DEBUG_PIDS:
            redo = '%-6d redo  ' % pid
        else:
            redo = 'redo  '
        self.file.write(
            ''.join([color, redo, env.v.DEPTH,
                     BOLD if color else '', s, PLAIN, '\n']))

    def write(self, s):
        """Write the string 's' to the log."""
        assert '\n' not in s
        sys.stdout.flush()
        sys.stderr.flush()
        g = REDO_RE.match(s)
        if g:
            capture = g.group(0)
            self.file.write(s[:-len(capture)])
            words = g.group(1).split(':')
            text = g.group(2)
            kind, pid, _ = words[0:3]
            pid = int(pid)
            if kind == 'unchanged':
                self._pretty(pid, '', '%s (unchanged)' % text)
            elif kind == 'check':
                self._pretty(pid, GREEN, '(%s)' % text)
            elif kind == 'do':
                self._pretty(pid, GREEN, text)
            elif kind == 'done':
                rv, name = text.split(' ', 1)
                rv = int(rv)
                if rv:
                    self._pretty(pid, RED, '%s (exit %d)' % (name, rv))
                elif env.v.VERBOSE or env.v.XTRACE or env.v.DEBUG:
                    self._pretty(pid, GREEN, '%s (done)' % name)
                    self.file.write('\n')
            elif kind == 'locked':
                if env.v.DEBUG_LOCKS:
                    self._pretty(pid, GREEN, '%s (locked...)' % text)
            elif kind == 'waiting':
                if env.v.DEBUG_LOCKS:
                    self._pretty(pid, GREEN, '%s (WAITING)' % text)
            elif kind == 'unlocked':
                if env.v.DEBUG_LOCKS:
                    self._pretty(pid, GREEN, '%s (...unlocked!)' % text)
            elif kind == 'error':
                self.file.write(''.join([RED, 'redo: ',
                                         BOLD, text, PLAIN, '\n']))
            elif kind == 'warning':
                self.file.write(''.join([YELLOW, 'redo: ',
                                         BOLD, text, PLAIN, '\n']))
            elif kind == 'debug':
                self._pretty(pid, '', text)
            else:
                assert 0, 'Unexpected @@REDO kind: %r' % kind
        else:
            self.file.write(s + '\n')
        self.file.flush()


_log = None

def setup(tty, parent_logs, pretty, color):
    global _log
    if pretty and not parent_logs:
        _check_tty(tty, color=color)
        _log = PrettyLog(tty=tty)
    else:
        _log = RawLog(tty=tty)


def write(s):
    _log.write(s)


def meta(kind, s, pid=None):
    assert ':' not in kind
    assert '@' not in kind
    assert '\n' not in s
    if pid is None:
        pid = os.getpid()
    write('@@REDO:%s:%d:%.4f@@ %s'
          % (kind, pid, time.time(), s))

def err(s):
    s = s.rstrip()
    meta('error', s)

def warn(s):
    s = s.rstrip()
    meta('warning', s)

def debug(s):
    if env.v.DEBUG >= 1:
        s = s.rstrip()
        meta('debug', s)

def debug2(s):
    if env.v.DEBUG >= 2:
        s = s.rstrip()
        meta('debug', s)

def debug3(s):
    if env.v.DEBUG >= 3:
        s = s.rstrip()
        meta('debug', s)
