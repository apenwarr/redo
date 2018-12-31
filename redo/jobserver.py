"""Implementation of a GNU make-compatible jobserver."""
#
# The basic idea is that both ends of a pipe (tokenfds) are shared with all
# subprocesses.  At startup, we write one "token" into the pipe for each
# configured job. (So eg. redo -j20 will put 20 tokens in the pipe.)  In
# order to do work, you must first obtain a token, by reading the other
# end of the pipe.  When you're done working, you write the token back into
# the pipe so that someone else can grab it.
#
# The toplevel process in the hierarchy is what creates the pipes in the
# first place.  Then it puts the pipe file descriptor numbers into MAKEFLAGS,
# so that subprocesses can pull them back out.
#
# As usual, edge cases make all this a bit tricky:
#
# - Every process is defined as owning a token at startup time.  This makes
#   sense because it's backward compatible with single-process make: if a
#   subprocess neither reads nor writes the pipe, then it has exactly one
#   token, so it's allowed to do one thread of work.
#
# - Thus, for symmetry, processes also must own a token at exit time.
#
# - In turn, to make *that* work, a parent process must destroy *its* token
#   upon launching a subprocess.  (Destroy, not release, because the
#   subprocess has created its own token.) It can try to obtain another
#   token, but if none are available, it has to stop work until one of its
#   subprocesses finishes.  When the subprocess finishes, its token is
#   destroyed, so the parent creates a new one.
#
# - If our process is going to stop and wait for a lock (eg. because we
#   depend on a target and someone else is already building that target),
#   we must give up our token.  Otherwise, we're sucking up a "thread" (a
#   unit of parallelism) just to do nothing.  If enough processes are waiting
#   on a particular lock, then the process building that target might end up
#   with only a single token, and everything gets serialized.
#
# - Unfortunately this leads to a problem: if we give up our token, we then
#   have to re-acquire a token before exiting, even if we want to exit with
#   an error code.
#
# - redo-log wants to linearize output so that it always prints log messages
#   in the order jobs were started; but because of the above, a job being
#   logged might end up with no tokens for a long time, waiting for some
#   other branch of the build to complete.
#
# As a result, we extend beyond GNU make's model and make things even more
# complicated.  We add a second pipe, cheatfds, which we use to "cheat" on
# tokens if our particular job is in the foreground (ie.  is the one
# currently being tailed by redo-log -f).  We add at most one token per
# redo-log instance.  If we are the foreground task, and we need a token,
# and we don't have a token, and we don't have any subtasks (because if we
# had a subtask, then we're not in the foreground), we synthesize our own
# token by incrementing _mytokens and _cheats, but we don't read from
# tokenfds.  Then, when it's time to give up our token again, we also won't
# write back to tokenfds, so the synthesized token disappears.
#
# Of course, all that then leads to *another* problem: every process must
# hold a *real* token when it exits, because its parent has given up a
# *real* token in order to start this subprocess.  If we're holding a cheat
# token when it's time to exit, then we can't meet this requirement.  The
# obvious thing to do would be to give up the cheat token and wait for a
# real token, but that might take a very long time, and if we're the last
# thing preventing our parent from exiting, then redo-log will sit around
# following our parent until we finally get a token so we can exit,
# defeating the whole purpose of cheating.  Instead of waiting, we write our
# "cheater" token to cheatfds.  Then, any task, upon noticing one of its
# subprocesses has finished, will check to see if there are any tokens on
# cheatfds; if so, it will remove one of them and *not* re-create its
# child's token, thus destroying the cheater token from earlier, and restoring
# balance.
#
# Sorry this is so complicated.  I couldn't think of a way to make it
# simpler :)
#
import sys, os, errno, select, fcntl, signal
from . import env, state, logs
from .atoi import atoi
from .helpers import close_on_exec

_toplevel = 0
_mytokens = 1
_cheats = 0
_tokenfds = None
_cheatfds = None
_waitfds = {}


def _debug(s):
    if 0:
        sys.stderr.write('job#%d: %s' % (os.getpid(), s))


def _create_tokens(n):
    """Materialize and own n tokens.

    If there are any cheater tokens active, they each destroy one matching
    newly-created token.
    """
    global _mytokens, _cheats
    assert n >= 0
    assert _cheats >= 0
    for _ in xrange(n):
        if _cheats > 0:
            _cheats -= 1
        else:
            _mytokens += 1


def _destroy_tokens(n):
    """Destroy n tokens that are currently in our posession."""
    global _mytokens
    assert _mytokens >= n
    _mytokens -= n


def _release(n):
    global _mytokens, _cheats
    assert n >= 0
    assert _mytokens >= n
    _debug('%d,%d -> release(%d)\n' % (_mytokens, _cheats, n))
    n_to_share = 0
    for _ in xrange(n):
        _mytokens -= 1
        if _cheats > 0:
            _cheats -= 1
        else:
            n_to_share += 1
    assert _mytokens >= 0
    assert _cheats >= 0
    if n_to_share:
        _debug('PUT tokenfds %d\n' % n_to_share)
        os.write(_tokenfds[1], 't' * n_to_share)


def _release_except_mine():
    assert _mytokens > 0
    _release(_mytokens - 1)


def release_mine():
    assert _mytokens >= 1
    _debug('%d,%d -> release_mine()\n' % (_mytokens, _cheats))
    _release(1)


def _timeout(sig, frame):
    pass


# We make the pipes use the first available fd numbers starting at startfd.
# This makes it easier to differentiate different kinds of pipes when using
# strace.
def _make_pipe(startfd):
    (a, b) = os.pipe()
    fds = (fcntl.fcntl(a, fcntl.F_DUPFD, startfd),
           fcntl.fcntl(b, fcntl.F_DUPFD, startfd + 1))
    os.close(a)
    os.close(b)
    return fds


def _try_read(fd, n):
    """Try to read n bytes from fd.  Returns: '' on EOF, None if EAGAIN."""
    assert state.is_flushed()

    # using djb's suggested way of doing non-blocking reads from a blocking
    # socket: http://cr.yp.to/unix/nonblock.html
    # We can't just make the socket non-blocking, because we want to be
    # compatible with GNU Make, and they can't handle it.
    r, w, x = select.select([fd], [], [], 0)
    if not r:
        return None  # try again
    # ok, the socket is readable - but some other process might get there
    # first.  We have to set an alarm() in case our read() gets stuck.
    oldh = signal.signal(signal.SIGALRM, _timeout)
    try:
        signal.setitimer(signal.ITIMER_REAL, 0.01, 0.01)  # emergency fallback
        try:
            b = os.read(fd, 1)
        except OSError, e:
            if e.errno in (errno.EAGAIN, errno.EINTR):
                # interrupted or it was nonblocking
                return None  # try again
            else:
                raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0, 0)
        signal.signal(signal.SIGALRM, oldh)
    return b


def _try_read_all(fd, n):
    bb = ''
    while 1:
        b = _try_read(fd, n)
        if not b:
            break
        bb += b
    return bb


def setup(maxjobs):
    """Start the jobserver (if it isn't already) with the given token count.

    Args:
      maxjobs: if nonzero, create a new jobserver with separate tokens from
        the one we inherited (if any).  If zero and we inherited a jobserver,
        just use that.  If zero and we didn't inherit a jobserver, create
        one with a default number of tokens (currently always 1).
    """
    global _tokenfds, _cheatfds, _toplevel
    assert maxjobs >= 0
    assert not _tokenfds
    _debug('setup(%d)\n' % maxjobs)

    flags = ' ' + os.getenv('MAKEFLAGS', '') + ' '
    FIND1 = ' --jobserver-auth='  # renamed in GNU make 4.2
    FIND2 = ' --jobserver-fds='   # fallback syntax
    FIND = FIND1
    ofs = flags.find(FIND1)
    if ofs < 0:
        FIND = FIND2
        ofs = flags.find(FIND2)
    if ofs >= 0:
        s = flags[ofs+len(FIND):]
        (arg, junk) = s.split(' ', 1)
        (a, b) = arg.split(',', 1)
        a = atoi(a)
        b = atoi(b)
        if a <= 0 or b <= 0:
            raise ValueError('invalid --jobserver-auth: %r' % arg)
        try:
            fcntl.fcntl(a, fcntl.F_GETFL)
            fcntl.fcntl(b, fcntl.F_GETFL)
        except IOError, e:
            if e.errno == errno.EBADF:
                raise ValueError('broken --jobserver-auth from make; ' +
                                 'prefix your Makefile rule with a "+"')
            else:
                raise
        if maxjobs == 1:
            # user requested exactly one token, which means they want to
            # serialize us, even if the parent redo is running in parallel.
            # That's pretty harmless, so allow it without a warning.
            pass
        elif maxjobs:
            # user requested more than one token, even though we have a parent
            # jobserver, which is fishy.  Warn about it, like make does.
            logs.warn(('warning: -j%d forced in sub-redo; ' +
                       'starting new jobserver.\n') % maxjobs)
        else:
            # user requested zero tokens, which means use the parent jobserver
            # if it exists.
            _tokenfds = (a, b)

    cheats = os.getenv('REDO_CHEATFDS', '') if not maxjobs else ''
    if cheats:
        (a, b) = cheats.split(',', 1)
        a = atoi(a)
        b = atoi(b)
        if a <= 0 or b <= 0:
            raise ValueError('invalid REDO_CHEATFDS: %r' % cheats)
        _cheatfds = (a, b)
    else:
        _cheatfds = _make_pipe(102)
        os.environ['REDO_CHEATFDS'] = ('%d,%d' % (_cheatfds[0], _cheatfds[1]))

    if not _tokenfds:
        # need to start a new server
        realmax = maxjobs or 1
        _toplevel = realmax
        _tokenfds = _make_pipe(100)
        _create_tokens(realmax - 1)
        _release_except_mine()
        os.environ['MAKEFLAGS'] = (
            ' -j --jobserver-auth=%d,%d --jobserver-fds=%d,%d' %
            (_tokenfds[0], _tokenfds[1],
             _tokenfds[0], _tokenfds[1]))


def _wait(want_token, max_delay):
    """Wait for a subproc to die or, if want_token, tokenfd to be readable.

    Does not actually read tokenfd once it's readable (so someone else might
    read it before us).  This function returns after max_delay seconds or
    when at least one subproc dies or (if want_token) for tokenfd to be
    readable.

    Args:
      want_token: true if we should return when tokenfd is readable.
      max_delay: max seconds to wait, or None to wait forever.
    Returns:
      None
    """
    rfds = _waitfds.keys()
    if want_token:
        rfds.append(_tokenfds[0])
    assert rfds
    assert state.is_flushed()
    _debug('_tokenfds=%r; jfds=%r\n' % (_tokenfds, _waitfds))
    r, w, x = select.select(rfds, [], [], max_delay)
    _debug('readable: %r\n' % (r,))
    for fd in r:
        if fd == _tokenfds[0]:
            pass
        else:
            pd = _waitfds[fd]
            _debug("done: %r\n" % pd.name)
            # redo subprocesses are expected to die without releasing their
            # tokens, so things are less likely to get confused if they
            # die abnormally.  Since a child has died, that means a token has
            # 'disappeared' and we now need to recreate it.
            b = _try_read(_cheatfds[0], 1)
            if b:
                # someone exited with _cheats > 0, so we need to compensate
                # by *not* re-creating a token now.
                _debug('EAT cheatfd %r\n' % b)
            else:
                _create_tokens(1)
                if has_token():
                    _release_except_mine()
            os.close(fd)
            del _waitfds[fd]
            rv = os.waitpid(pd.pid, 0)
            assert rv[0] == pd.pid
            _debug("done1: rv=%r\n" % (rv,))
            rv = rv[1]
            if os.WIFEXITED(rv):
                pd.rv = os.WEXITSTATUS(rv)
            else:
                pd.rv = -os.WTERMSIG(rv)
            _debug("done2: rv=%d\n" % pd.rv)
            pd.donefunc(pd.name, pd.rv)


def has_token():
    """Returns true if this process has a job token."""
    assert _mytokens >= 0
    if _mytokens >= 1:
        return True


def _ensure_token(reason, max_delay=None):
    """Don't return until this process has a job token.

    Args:
      reason: the reason (for debugging purposes) we need a token.  Usually
        the name of a target we want to build.
      max_delay: the max time to wait for a token, or None if forever.
    Returns:
      None, but has_token() is now true *unless* max_delay is non-None
      and we timed out.
    """
    global _mytokens
    assert state.is_flushed()
    assert _mytokens <= 1
    while 1:
        if _mytokens >= 1:
            _debug("_mytokens is %d\n" % _mytokens)
            assert _mytokens == 1
            _debug('(%r) used my own token...\n' % reason)
            break
        assert _mytokens < 1
        _debug('(%r) waiting for tokens...\n' % reason)
        _wait(want_token=1, max_delay=max_delay)
        if _mytokens >= 1:
            break
        assert _mytokens < 1
        b = _try_read(_tokenfds[0], 1)
        if b == '':
            raise Exception('unexpected EOF on token read')
        if b:
            _mytokens += 1
            _debug('(%r) got a token (%r).\n' % (reason, b))
            break
        if max_delay != None:
            break
    assert _mytokens <= 1


def ensure_token_or_cheat(reason, cheatfunc):
    """Wait for a job token to become available, or cheat if possible.

    If we already have a token, we return immediately.  If we have any
    processes running *and* we don't own any tokens, we wait for a process
    to finish, and then use that token.

    Otherwise, we're allowed to cheat.  We call cheatfunc() occasionally
    to consider cheating; if it returns n > 0, we materialize that many
    cheater tokens and return.

    Args:
      reason: the reason (for debugging purposes) we need a token.  Usually
        the name of a target we want to build.
      cheatfunc: a function which returns n > 0 (usually 1) if we should
        cheat right now, because we're the "foreground" process that must
        be allowed to continue.
    """
    global _mytokens, _cheats
    backoff = 0.01
    while not has_token():
        while running() and not has_token():
            # If we already have a subproc running, then effectively we
            # already have a token.  Don't create a cheater token unless
            # we're completely idle.
            _ensure_token(reason, max_delay=None)
        _ensure_token(reason, max_delay=min(1.0, backoff))
        backoff *= 2
        if not has_token():
            assert _mytokens == 0
            n = cheatfunc()
            _debug('%s: %s: cheat = %d\n' % (env.v.TARGET, reason, n))
            if n > 0:
                _mytokens += n
                _cheats += n
                break


def running():
    """Returns true if we have any running jobs."""
    return len(_waitfds)


def wait_all():
    """Wait for all running jobs to finish."""
    _debug("%d,%d -> wait_all\n" % (_mytokens, _cheats))
    assert state.is_flushed()
    while 1:
        while _mytokens >= 2:
            _release(1)
        if not running():
            break
        # We should only release our last token if we have remaining
        # children.  A terminating redo process should try to terminate while
        # holding a token, and if we have no children left, we might be
        # about to terminate.
        if _mytokens >= 1:
            release_mine()
        _debug("wait_all: wait()\n")
        _wait(want_token=0, max_delay=None)
    _debug("wait_all: empty list\n")
    if _toplevel:
        # If we're the toplevel and we're sure no child processes remain,
        # then we know we're totally idle.  Self-test to ensure no tokens
        # mysteriously got created/destroyed.
        if _mytokens >= 1:
            release_mine()
        tokens = _try_read_all(_tokenfds[0], 8192)
        cheats = _try_read_all(_cheatfds[0], 8192)
        _debug('toplevel: GOT %d tokens and %d cheats\n'
               % (len(tokens), len(cheats)))
        if len(tokens) - len(cheats) != _toplevel:
            raise Exception('on exit: expected %d tokens; found %r-%r'
                            % (_toplevel, len(tokens), len(cheats)))
        os.write(_tokenfds[1], tokens)
    # note: when we return, we may have *no* tokens, not even our own!
    # If caller wants to continue, they might have to obtain one first.


def force_return_tokens():
    """Release or destroy all the tokens we own, in preparation for exit."""
    n = len(_waitfds)
    _debug('%d,%d -> %d jobs left in force_return_tokens\n'
           % (_mytokens, _cheats, n))
    for k in list(_waitfds):
        del _waitfds[k]
    _create_tokens(n)
    if has_token():
        _release_except_mine()
        assert _mytokens == 1, 'mytokens=%d' % _mytokens
    assert _cheats <= _mytokens, 'mytokens=%d cheats=%d' % (_mytokens, _cheats)
    assert _cheats in (0, 1), 'cheats=%d' % _cheats
    if _cheats:
        _debug('%d,%d -> force_return_tokens: recovering final token\n'
               % (_mytokens, _cheats))
        _destroy_tokens(_cheats)
        os.write(_cheatfds[1], 't' * _cheats)
    assert state.is_flushed()


class Job(object):
    """Metadata about a running job."""

    def __init__(self, name, pid, donefunc):
        """Initialize a job.

        Args:
          name: the name of the job (usually a target filename).
          pid: the pid of the subprocess running this job.
          donefunc: the function(name, return_value) to call when the
            subprocess exits.
        """
        self.name = name
        self.pid = pid
        self.rv = None
        self.donefunc = donefunc

    def __repr__(self):
        return 'Job(%s,%d)' % (self.name, self.pid)


def start(reason, jobfunc, donefunc):
    """Start a new job.  Must only be run with has_token() true.

    Args:
      reason: the reason the job is running.  Usually the filename of a
        target being built.
      jobfunc: the function() to execute, **in a subprocess**, to run the job.
        Usually this calls os.execve().  It is an error for this function to
        ever return.  If it does, we return a non-zero exit code to the parent
        process (the one which ran start()).
      donefunc: the function(reason, return_value) to call **in the parent**
        when the subprocess exits.
    """
    assert state.is_flushed()
    assert _mytokens <= 1
    assert _mytokens == 1
    # Subprocesses always start with 1 token, so we have to destroy ours
    # in order for the universe to stay in balance.
    _destroy_tokens(1)
    r, w = _make_pipe(50)
    pid = os.fork()
    if pid == 0:
        # child
        rv = 201
        try:
            os.close(r)
            try:
                rv = jobfunc()
                assert 0, 'jobfunc returned?! (%r, %r)' % (jobfunc, rv)
            except Exception:  # pylint: disable=broad-except
                import traceback
                traceback.print_exc()
        finally:
            _debug('exit: %d\n' % rv)
            os._exit(rv)
    close_on_exec(r, True)
    os.close(w)
    pd = Job(reason, pid, donefunc)
    _waitfds[r] = pd
