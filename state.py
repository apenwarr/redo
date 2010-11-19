import sys, os, errno
import vars
from helpers import unlink, relpath, debug2


def _sname(typ, t, fromdir=None):
    # FIXME: t.replace(...) is non-reversible and non-unique here!
    if fromdir:
        t = os.path.join(fromdir, t)
    tnew = relpath(t, vars.BASE)
    v = vars.BASE + ('/.redo/%s^%s' % (typ, tnew.replace('/', '^')))
    debug2('sname: (%r) %r -> %r\n' % (os.getcwd(), t, tnew))
    return v


def add_dep(t, mode, dep):
    debug2('add-dep(%r)\n' % t)
    open(_sname('dep', t), 'a').write('%s %s\n'
                                      % (mode, relpath(dep, vars.BASE)))


def deps(t, fromdir=None):
    for line in open(_sname('dep', t, fromdir)).readlines():
        assert(line[0] in ('c','m'))
        assert(line[1] == ' ')
        assert(line[-1] == '\n')
        mode = line[0]
        name = line[2:-1]
        yield mode,name


def _stampname(t, fromdir=None):
    return _sname('stamp', t, fromdir)
    

def stamp(t):
    stampfile = _stampname(t)
    newstampfile = _sname('stamp' + str(os.getpid()), t)
    depfile = _sname('dep', t)
    if not os.path.exists(vars.BASE + '/.redo'):
        # .redo might not exist in a 'make clean' target
        return
    open(newstampfile, 'w').close()
    try:
        mtime = os.stat(t).st_mtime
    except OSError:
        mtime = 0
    os.utime(newstampfile, (mtime, mtime))
    os.rename(newstampfile, stampfile)
    open(depfile, 'a').close()


def unstamp(t, fromdir=None):
    unlink(_stampname(t, fromdir))


def stamped(t, fromdir=None):
    try:
        stamptime = os.stat(_stampname(t, fromdir)).st_mtime
    except OSError, e:
        if e.errno == errno.ENOENT:
            return None
        else:
            raise
    return stamptime


def is_generated(t):
    return os.path.exists(_sname('gen', t))


def start(t):
    open(_sname('dep', t), 'w').close()
    open(_sname('gen', t), 'w').close()  # it's definitely a generated file


class Lock:
    def __init__(self, t):
        self.lockname = _sname('lock', t)
        self.owned = False

    def __del__(self):
        if self.owned:
            self.unlock()

    def lock(self):
        try:
            os.mkfifo(self.lockname, 0600)
            self.owned = True
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

    def unlock(self):
        if not self.owned:
            raise Exception("can't unlock %r - we don't own it" 
                            % self.lockname)
        fd = None
        try:
            fd = os.open(self.lockname, os.O_WRONLY|os.O_NONBLOCK)
        except OSError, e:
            if e.errno == errno.ENXIO: # no readers open; that's ok
                pass
            elif e.errno == errno.ENOENT: # 'make clean' might do this
                pass
            else:
                raise
        unlink(self.lockname)  # make sure no new readers can connect
        if fd != None: os.close(fd)  # now unlock any existing readers
        self.owned = False

    def wait(self):
        if self.owned:
            raise Exception("can't wait on %r - we own it" % self.lockname)
        try:
            # open() will finish only when a writer exists and does close()
            os.close(os.open(self.lockname, os.O_RDONLY))
            #sys.stderr.write('lock %r waited ok\n' % self.lockname)
        except OSError, e:
            if e.errno == errno.ENOENT:
                #sys.stderr.write('lock %r missing\n' % self.lockname)
                pass  # it's not even unlocked or was unlocked earlier
            else:
                raise
