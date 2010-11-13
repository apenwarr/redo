#!/usr/bin/python
#
# beware the jobberwack
#
import sys, os, errno, select, subprocess, fcntl
import options
from helpers import *

optspec = """
jwack [-j maxjobs] -- <command...>
--
j,jobs=    maximum jobs to run at once
"""

_fds = None
_tokens = {}
_waitfds = {}
_fake_token = 0


def _release(n):
    global _fake_token
    if _fake_token:
        _fake_token = 0
        n -= 1
    os.write(_fds[1], 't' * n)


def setup(maxjobs):
    global _fds
    if _fds:
        return  # already set up
    flags = ' ' + os.getenv('MAKEFLAGS', '') + ' '
    FIND = ' --jobserver-fds='
    ofs = flags.find(FIND)
    if ofs >= 0:
        s = flags[ofs+len(FIND):]
        (arg,junk) = s.split(' ', 1)
        (a,b) = arg.split(',', 1)
        a = atoi(a)
        b = atoi(b)
        if a <= 0 or b <= 0:
            raise ValueError('invalid --jobserver-fds: %r' % arg)
        _fds = (a,b)
    if maxjobs and not _fds:
        # need to start a new server
        _fds = os.pipe()
        _release(maxjobs)
        os.putenv('MAKEFLAGS',
                  '%s --jobserver-fds=%d,%d -j' % (os.getenv('MAKEFLAGS'),
                                                    _fds[0], _fds[1]))


def wait(want_token):
    rfds = _waitfds.keys()
    if _fds and want_token:
        rfds.append(_fds[0])
    r,w,x = select.select(rfds, [], [])
    #print 'readable: %r' % r
    for fd in r:
        if _fds and fd == _fds[0]:
            pass
        else:
            p = _waitfds[fd]
            _release(_tokens[fd])
            b = os.read(fd, 1)
            #print 'read: %r' % b
            if b:
                #print 'giving up %d tokens for child' % _tokens[fd]
                _tokens[fd] = 0
            else:
                os.close(fd)
                del _waitfds[fd]
                del _tokens[fd]
                p.wait()


def wait_for_token():
    pfd = atoi(os.getenv('JWACK_PARENT_FD', ''))
    #print 'pfd is %d' % pfd
    if pfd:
        # tell parent jwack to give back his token
        os.write(pfd, 'j')
    else:
        # parent is a "real" GNU make.  He'll assume we already have a token,
        # so manufacture one and don't bother waiting.
        global _fake_token
        _fake_token = 1
        return
    while 1:
        print 'waiting for tokens...'
        wait(want_token=1)
        if _fds:
            fcntl.fcntl(_fds[0], fcntl.F_SETFL, os.O_NONBLOCK)
            try:
                b = os.read(_fds[0], 1)  # FIXME try: block
            except OSError, e:
                if e.errno == errno.EAGAIN:
                    b = ''
                    pass
                else:
                    raise
            if b:
                break
    print 'got a token (%r).' % b


def wait_all():
    while _waitfds:
        wait(want_token=0)


def force_return_tokens():
    n = sum(_tokens.values())
    print 'returning %d tokens' % n
    if _fds:
        _release(n)
        for k in _tokens.keys():
            _tokens[k] = 0


def _pre_job(r,w):
    os.putenv('JWACK_PARENT_FD', str(w))
    os.close(r)
    

def start_job(argv, stdout=None):
    global _mytokens
    setup(1)
    if stdout:
        argx = dict(stdout=stdout)
    else:
        argx = dict()
    wait_for_token()
    r,w = os.pipe()
    p = subprocess.Popen(argv, preexec_fn=lambda: _pre_job(r,w), **argx)
    os.close(w)
    _waitfds[r] = p
    _tokens[r] = 1
    return p
    

def main():
    o = options.Options('jwack', optspec)
    (opt, flags, extra) = o.parse(sys.argv[1:])

    if not extra:
        o.fatal("no command line given")

    setup(opt.jobs)
    try:
        p = start_job(extra)
        wait_all()
        return p.wait()
    finally:
        force_return_tokens()


if __name__ == "__main__":
    sys.exit(main())
