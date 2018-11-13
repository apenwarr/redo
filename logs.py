import os, re, sys, time
import vars


def check_tty():
    global RED, GREEN, YELLOW, BOLD, PLAIN
    if sys.stderr.isatty() and (os.environ.get('TERM') or 'dumb') != 'dumb':
        # ...use ANSI formatting codes.
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
    def __init__(self, file):
        self.file = file

    def write(self, s):
        assert('\n' not in s)
        sys.stdout.flush()
        sys.stderr.flush()
        self.file.write(s + '\n')
        self.file.flush()


REDO_RE = re.compile(r'@@REDO:([^@]+)@@ (.*)$')


class PrettyLog(object):
    def __init__(self, file):
        self.file = file
    
    def _pretty(self, pid, color, s):
        if vars.DEBUG_PIDS:
            redo = '%d redo  ' % pid
        else:
            redo = 'redo  '
        self.file.write(''.join([color, redo, vars.DEPTH,
                                  BOLD if color else '', s, PLAIN, '\n']))

    def write(self, s):
        assert('\n' not in s)
        sys.stdout.flush()
        sys.stderr.flush()
        g = REDO_RE.match(s)
        if g:
            # FIXME: support vars.DEBUG_PIDS somewhere
            all = g.group(0)
            self.file.write(s[:-len(all)])
            words = g.group(1).split(':')
            text = g.group(2)
            kind, pid, when = words[0:3]
            if kind == 'unchanged':
                if vars.DEBUG >= 1:
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
                elif vars.VERBOSE or vars.XTRACE or vars.DEBUG:
                    self._pretty(pid, GREEN, '%s (done)' % name)
                    self.file.write('\n')
            elif kind == 'locked':
                if vars.DEBUG_LOCKS:
                    self._pretty(pid, GREEN, '%s (locked...)' % text)
            elif kind == 'waiting':
                if vars.DEBUG_LOCKS:
                    self._pretty(pid, GREEN, '%s (WAITING)' % text)
            elif kind == 'unlocked':
                if vars.DEBUG_LOCKS:
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

def setup(file, pretty):
    global _log
    if pretty:
        check_tty()
        _log = PrettyLog(file=file)
    else:
        _log = RawLog(file=file)


# FIXME: explicitly initialize in each program
setup(file=sys.stderr, pretty=False)


def write(s):
    _log.write(s)


def meta(kind, s):
    _log.meta(kind, s)


def meta(kind, s):
    assert(':' not in kind)
    assert('@' not in kind)
    assert('\n' not in s)
    write('@@REDO:%s:%d:%.4f@@ %s'
          % (kind, os.getpid(), time.time(), s))

def err(s):
    s = s.rstrip()
    meta('error', s)

def warn(s):
    s = s.rstrip()
    meta('warning', s)

def debug(s):
    if vars.DEBUG >= 1:
        s = s.rstrip()
        meta('debug', s)

def debug2(s):
    if vars.DEBUG >= 2:
        s = s.rstrip()
        meta('debug', s)

def debug3(s):
    if vars.DEBUG >= 3:
        s = s.rstrip()
        meta('debug', s)
