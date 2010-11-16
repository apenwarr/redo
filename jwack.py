#
# beware the jobberwack
#
import sys, os, errno, select, fcntl
import atoi

_toplevel = 0
_mytokens = 1
_fds = None
_waitfds = {}


def _debug(s):
    if 0:
        sys.stderr.write('jwack#%d: %s' % (os.getpid(),s))
    

def _release(n):
    global _mytokens
    _debug('release(%d)\n' % n)
    _mytokens += n
    if _mytokens > 1:
        os.write(_fds[1], 't' * (_mytokens-1))
        _mytokens = 1


def _try_read(fd, n):
    # FIXME: this isn't actually safe, because GNU make can't handle it if
    # the socket is nonblocking.  Ugh.  That means we'll have to do their
    # horrible SIGCHLD hack after all.
    fcntl.fcntl(_fds[0], fcntl.F_SETFL, os.O_NONBLOCK)
    try:
        try:
            b = os.read(_fds[0], 1)
        except OSError, e:
            if e.errno == errno.EAGAIN:
                return ''
            else:
                raise
    finally:
        fcntl.fcntl(_fds[0], fcntl.F_SETFL, 0)
    return b and b or None


def setup(maxjobs):
    global _fds, _toplevel
    if _fds:
        return  # already set up
    _debug('setup(%d)\n' % maxjobs)
    flags = ' ' + os.getenv('MAKEFLAGS', '') + ' '
    FIND = ' --jobserver-fds='
    ofs = flags.find(FIND)
    if ofs >= 0:
        s = flags[ofs+len(FIND):]
        (arg,junk) = s.split(' ', 1)
        (a,b) = arg.split(',', 1)
        a = atoi.atoi(a)
        b = atoi.atoi(b)
        if a <= 0 or b <= 0:
            raise ValueError('invalid --jobserver-fds: %r' % arg)
        try:
            fcntl.fcntl(a, fcntl.F_GETFL)
            fcntl.fcntl(b, fcntl.F_GETFL)
        except IOError, e:
            if e.errno == errno.EBADF:
                raise ValueError('broken --jobserver-fds from make; prefix your Makefile rule with a "+"')
            else:
                raise
        _fds = (a,b)
    if maxjobs and not _fds:
        # need to start a new server
        _toplevel = maxjobs
        _fds = os.pipe()
        _release(maxjobs-1)
        os.putenv('MAKEFLAGS',
                  '%s --jobserver-fds=%d,%d -j' % (os.getenv('MAKEFLAGS'),
                                                    _fds[0], _fds[1]))


def wait(want_token):
    rfds = _waitfds.keys()
    if _fds and want_token:
        rfds.append(_fds[0])
    r,w,x = select.select(rfds, [], [])
    _debug('_fds=%r; wfds=%r; readable: %r\n' % (_fds, _waitfds, r))
    for fd in r:
        if _fds and fd == _fds[0]:
            pass
        else:
            pd = _waitfds[fd]
            _debug("done: %r\n" % pd.name)
            _release(1)
            os.close(fd)
            del _waitfds[fd]
            rv = os.waitpid(pd.pid, 0)
            assert(rv[0] == pd.pid)
            rv = rv[1]
            if os.WIFEXITED(rv):
                pd.rv = os.WEXITSTATUS(rv)
            else:
                pd.rv = -os.WTERMSIG(rv)


def get_token(reason):
    global _mytokens
    while 1:
        if _mytokens >= 1:
            _debug('(%r) used my own token...\n' % reason)
            _mytokens -= 1
            return
        _debug('(%r) waiting for tokens...\n' % reason)
        wait(want_token=1)
        if _fds:
            b = _try_read(_fds[0], 1)
            if b == None:
                raise Exception('unexpected EOF on token read')
            if b:
                break
    _debug('(%r) got a token (%r).\n' % (reason, b))


def wait_all():
    _debug("wait_all\n")
    while _waitfds:
        _debug("wait_all: wait()\n")
        wait(want_token=0)
    _debug("wait_all: empty list\n")
    if _toplevel:
        bb = ''
        while 1:
            b = _try_read(_fds[0], 8192)
            bb += b
            if not b: break
        if len(bb) != _toplevel-1:
            raise Exception('on exit: expected %d tokens; found only %d' 
                            % (_toplevel-1, len(b)))
    _debug("wait_all: done\n")


def force_return_tokens():
    n = len(_waitfds)
    if n:
        _debug('%d tokens left in force_return_tokens\n' % n)
    _debug('returning %d tokens\n' % n)
    for k in _waitfds.keys():
        del _waitfds[k]
    if _fds:
        _release(n)


def _pre_job(r, w, pfn):
    os.close(r)
    if pfn:
        pfn()


class Job:
    def __init__(self, name, pid):
        self.name = name
        self.pid = pid
        self.rv = None

            
def start_job(reason, jobfunc):
    setup(1)
    get_token(reason)
    r,w = os.pipe()
    pid = os.fork()
    if pid == 0:
        # child
        os.close(r)
        try:
            try:
                jobfunc()
                os._exit(0)
            except Exception, e:
                sys.stderr.write("Exception: %s\n" % e)
        finally:
            os._exit(201)
    # else we're the parent process
    os.close(w)
    pd = Job(reason, pid)
    _waitfds[r] = pd
    return pd
