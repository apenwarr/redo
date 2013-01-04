import sys, os, errno, glob, stat, fcntl
import vars
from helpers import unlink, join, close_on_exec
from log import warn, err, debug, debug2, debug3

ALWAYS = '//ALWAYS'   # an invalid filename that is always marked as dirty
STAMP_DIR = 'dir'     # the stamp of a directory; mtime is unhelpful
STAMP_MISSING = '0'   # the stamp of a nonexistent file


def fix_chdir(targets):
    """Undo any chdir() done by the .do script that called us.

    When we run a .do script, we do it from the directory containing that .do
    script, which is represented by STARTDIR/PWD (ie. the redo start directory
    plus any relative path of the current script).  However, the .do script
    is allowed to do chdir() and then run various redo commands.  We need
    to be running in well-defined conditions, so we chdir() to the original
    STARTDIR/PWD and paraphrase all the command-line arguments (targets) into
    paths relative to that directory.

    Args:
      targets: almost always sys.argv[1:]; paths relative to os.getcwd().
    Returns:
      targets, but relative to the (newly changed) os.getcwd().
    """
    abs_pwd = os.path.join(vars.STARTDIR, vars.PWD)
    if os.path.samefile('.', abs_pwd):
        return targets  # nothing to change
    rel_orig_dir = os.path.relpath('.', abs_pwd)
    os.chdir(abs_pwd)
    return [os.path.join(rel_orig_dir, t) for t in targets]


def _files(target, seen):
    dir = os.path.dirname(target)
    f = File(target)
    if f.name not in seen:
        seen[f.name] = 1
        yield f
    for stamp, dep in f.deps:
        fullname = os.path.join(dir, dep)
        for i in _files(fullname, seen):
            yield i


def files():
    """Return a list of files known to redo, starting in os.getcwd()."""
    seen = {}
    for depfile in glob.glob('*.deps.redo'):
        for i in _files(depfile[:-10], seen):
            yield i

# FIXME: I really want to use fcntl F_SETLK, F_SETLKW, etc here.  But python
# doesn't do the lockdata structure in a portable way, so we have to use
# fcntl.lockf() instead.  Usually this is just a wrapper for fcntl, so it's
# ok, but it doesn't have F_GETLK, so we can't report which pid owns the lock.
# The makes debugging a bit harder.  When we someday port to C, we can do that.
class LockHelper:
    def __init__(self, lock, kind):
        self.lock = lock
        self.kind = kind

    def __enter__(self):
        self.oldkind = self.lock.owned
        if self.kind != self.oldkind:
            self.lock.waitlock(self.kind)

    def __exit__(self, type, value, traceback):
        if self.kind == self.oldkind:
            pass
        elif self.oldkind:
            self.lock.waitlock(self.oldkind)
        else:
            self.lock.unlock()

LOCK_EX = fcntl.LOCK_EX
LOCK_SH = fcntl.LOCK_SH

class Lock:
    def __init__(self, name):
        self.owned = False
        self.name  = name
        self.lockfile = os.open(self.name, os.O_RDWR | os.O_CREAT, 0666)
        close_on_exec(self.lockfile, True)
        self.shared = fcntl.LOCK_SH
        self.exclusive = fcntl.LOCK_EX

    def __del__(self):
        if self.owned:
            self.unlock()
        os.close(self.lockfile)

    def read(self):
        return LockHelper(self, fcntl.LOCK_SH)

    def write(self):
        return LockHelper(self, fcntl.LOCK_EX)

    def trylock(self, kind=fcntl.LOCK_EX):
        assert(self.owned != kind)
        try:
            fcntl.lockf(self.lockfile, kind|fcntl.LOCK_NB, 0, 0)
        except IOError, e:
            if e.errno in (errno.EAGAIN, errno.EACCES):
                if vars.DEBUG_LOCKS: debug("%s lock failed\n", self.name)
                pass  # someone else has it locked
            else:
                raise
        else:
            if vars.DEBUG_LOCKS: debug("%s lock\n", self.name)
            self.owned = kind

    def waitlock(self, kind=fcntl.LOCK_EX):
        assert(self.owned != kind)
        if vars.DEBUG_LOCKS: debug("%s lock\n", self.name)
        fcntl.lockf(self.lockfile, kind, 0, 0)
        self.owned = kind

    def unlock(self):
        if not self.owned:
            raise Exception("can't unlock %r - we don't own it" % self.name)
        fcntl.lockf(self.lockfile, fcntl.LOCK_UN, 0, 0)
        if vars.DEBUG_LOCKS: debug("%s unlock\n", self.name)
        self.owned = False

class File(object):
    def __init__(self, name, context=None):
        if name != ALWAYS and context:
            name = os.path.join(context, name)
        if name != ALWAYS and name.startswith('/'):
            name = os.path.relpath(name, os.getcwd())
        self.name = name
        self.dir = os.path.split(self.name)[0]
        if name != ALWAYS:
            self.redo_dir = self._get_redodir(name)
            try: os.makedirs(self.redo_dir)
            except: pass
            self.read_only = not os.path.isdir(self.redo_dir)
            if not self.read_only:
                self.dolock = Lock(self.tmpfilename("do.lock"))
        self.refresh()

    def __repr__(self):
        return 'state.File(%s)' % self.name

    def _get_redodir(self, name):
        d = os.path.dirname(name)
        #r = [".redo"]
        #while not os.path.isdir(d):
        #    d, sep, base = d.rpartition.split('/')
        #    if not sep: break
        #    r.append("%s.redo" % base)
        #return os.path.join(d, *r)
        return os.path.join(d, ".redo")

    def tmpfilename(self, filetype):
        name = os.path.basename(self.name)
        return '%s.%s' % (os.path.join(self.redo_dir, name), filetype)

    def printable_name(self):
        """Return the name relative to vars.STARTDIR, normalized.

        "normalized" means we use os.path.normpath(), but only if that doesn't
        change the meaning of the filename.  (If there are symlinks,
        simplifying a/b/../c into a/c might not be correct.)

        The result is suitable for printing in the output, where all filenames
        will be relative to the user's starting directory, regardless of
        which .do file we're in or the getcwd() of the moment.
        """
        base = os.path.join(vars.PWD, self.name)
        base_full_dir = os.path.dirname(os.path.join(vars.STARTDIR, base))
        norm = os.path.normpath(base)
        norm_full_dir = os.path.dirname(os.path.join(vars.STARTDIR, norm))
        try:
            if os.path.samefile(base_full_dir, norm_full_dir):
                return norm
        except OSError:
            pass
        return base

    def refresh(self):
        if self.name == ALWAYS:
            self.stamp_mtime = str(vars.RUNID)
            self.exitcode = 0
            self.deps = []
            self.is_generated = True
            self.csum = None
            self.stamp = str(vars.RUNID)
            return
        assert(not self.name.startswith('/'))
        try:
            # read the state file
            f = open(self.tmpfilename('deps'))
        except IOError:
            try:
                # okay, check for the file itself
                st = os.stat(self.name)
            except OSError:
                # it doesn't exist at all yet
                self.stamp_mtime = 0  # no stamp file
                self.exitcode = 0
                self.deps = []
                self.stamp = STAMP_MISSING
                self.csum = None
                self.is_generated = True
            else:
                # it's a source file (without a .deps file)
                self.stamp_mtime = 0  # no stamp file
                self.exitcode = 0
                self.deps = []
                self.is_generated = False
                self.csum = None
                self.stamp = self.read_stamp(st=st)
        else:
            # it's a target (with a .deps file)
            st = os.fstat(f.fileno())
            lines = f.read().strip().split('\n')
            self.stamp_mtime = int(st.st_mtime)
            self.exitcode = int(lines.pop(-1))
            self.is_generated = True
            self.csum = None
            self.stamp = lines.pop(-1)
            self.deps = [line.split(' ', 1) for line in lines]
            # if the next line fails, it means that the .dep file is not
            # correctly formatted
            while self.deps and self.deps[-1][1] == '.':
                # a line added by redo-stamp
                self.csum = self.deps.pop(-1)[0]

    def exists(self):
        return os.path.exists(self.name)

    def exists_not_dir(self):
        return os.path.exists(self.name) and not os.path.isdir(self.name)

    def forget(self):
        """Turn a 'target' file back into a 'source' file."""
        debug3('forget(%s)\n', self.name)
        unlink(self.tmpfilename('deps'))

    def _add(self, line):
        depsname = self.tmpfilename('deps2')
        debug3('_add(%s) to %r\n', line, depsname)
        #assert os.path.exists(depsname)
        line = str(line)
        f = open(depsname, 'a')
        assert('\n' not in line)
        f.write(line + '\n')

    def build_starting(self):
        """Call this when you're about to start building this target."""
        assert self.dolock.owned == self.dolock.exclusive
        depsname = self.tmpfilename('deps2')
        debug3('build starting: %r\n', depsname)
        unlink(depsname)

    def build_done(self, exitcode):
        """Call this when you're done building this target."""
        assert self.dolock.owned == self.dolock.exclusive
        depsname = self.tmpfilename('deps2')
        debug3('build ending: %r\n', depsname)
        self._add(self.read_stamp(runid=vars.RUNID))
        self._add(exitcode)
        os.utime(depsname, (vars.RUNID, vars.RUNID))
        os.rename(depsname, self.tmpfilename('deps'))

    def add_dep(self, file):
        """Mark the given File() object as a dependency of this target.

        The filesystem file it refers to may or may not exist.  If it doesn't
        exist, creating the file is considered a "modified" event and will
        result in this target being rebuilt.
        """
        relname = os.path.relpath(file.name, self.dir)
        debug3('add-dep: %r < %r %r\n', self.name, file.stamp, relname)
        assert('\n' not in file.name)
        assert(' '  not in file.stamp)
        assert('\n' not in file.stamp)
        assert('\t' not in file.stamp)
        assert('\r' not in file.stamp)
        self._add('%s %s' % (file.csum or file.stamp, relname))

    def read_stamp(self, runid=None, st=None, st_deps=None):
        # FIXME: make this formula more well-defined
        if runid is None:
            if st_deps == None:
                try: st_deps = os.stat(self.tmpfilename('deps'))
                except OSError: st_deps = False

            if st_deps == False:
                runid_suffix = ''
            else:
                runid_suffix = '+' + str(int(st_deps.st_mtime))
        else:
            runid_suffix = '+' + str(int(runid))

        if st == None:
            try: st = os.stat(self.name)
            except OSError: st = False

        if st == False:
            return STAMP_MISSING + runid_suffix
        if stat.S_ISDIR(st.st_mode):
            return STAMP_DIR + runid_suffix
        else:
            # a "unique identifier" stamp for a regular file
            return join('-', (st.st_ctime, st.st_mtime,
                              st.st_size, st.st_ino)) + runid_suffix


def is_missing(stamp):
    if not stamp:
        return False
    return stamp == STAMP_MISSING or stamp.startswith(STAMP_MISSING + '+')
