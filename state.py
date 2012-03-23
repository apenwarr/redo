import sys, os, errno, glob, stat
import vars
from helpers import unlink, join
from log import warn, err, debug2, debug3

# When the module is imported, change the process title.
# We do it here because this module is imported by all the scripts.
try:
	from setproctitle import setproctitle
except ImportError:
	pass
else:
	cmdline = sys.argv[:]
	cmdline[0] = os.path.splitext(os.path.basename(cmdline[0]))[0]
	setproctitle(" ".join(cmdline))

ALWAYS = '//ALWAYS'   # an invalid filename that is always marked as dirty
STAMP_DIR = 'dir'     # the stamp of a directory; mtime is unhelpful
STAMP_MISSING = '0'   # the stamp of a nonexistent file


def warn_override(name):
    warn('%s - you modified it; skipping\n', name)


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
    if vars.SHUFFLE:
        import random
        random.shuffle(targets)
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


class File(object):
    def __init__(self, name):
        if name != ALWAYS and name.startswith('/'):
            name = os.path.relpath(name, os.getcwd())
        self.name = name
        self.dir = os.path.split(self.name)[0]
        self._file_prefix = None
        self.refresh()

    def __repr__(self):
        return 'state.File(%s)' % self.name

    def tmpfilename(self, filetype):
        return '%s.%s.redo' % (self._file_prefix or self.name, filetype)

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
                self.stamp = self.read_stamp()
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
            while self.deps and self.deps[-1][1] == '.':
                # a line added by redo-stamp
                self.csum = self.deps.pop(-1)[0]

    def exists(self):
        return os.path.exists(self.name)

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
        self._file_prefix = self.name
        while 1:
            depsname = self.tmpfilename('deps2')
            if os.path.isdir(os.path.join(os.path.dirname(depsname), '.')):
                break
            parts = self._file_prefix.split('/')
            parts = parts[:-2] + [parts[-2] + '__' + parts[-1]]
            self._file_prefix = os.path.join(*parts)
        debug3('build starting: %r\n', depsname)
        unlink(depsname)

    def build_done(self, exitcode):
        """Call this when you're done building this target."""
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

    def read_stamp(self, runid=None):
        # FIXME: make this formula more well-defined
        if runid is None:
            try:
                st_deps = os.stat(self.tmpfilename('deps'))
            except OSError:
                runid_suffix = ''
            else:
                runid_suffix = '+' + str(int(st_deps.st_mtime))
        else:
            runid_suffix = '+' + str(int(runid))
        try:
            st = os.stat(self.name)
        except OSError:
            return STAMP_MISSING + runid_suffix
        if stat.S_ISDIR(st.st_mode):
            return STAMP_DIR + runid_suffix
        else:
            # a "unique identifier" stamp for a regular file
            return join('-', (st.st_ctime, st.st_mtime,
                              st.st_size, st.st_ino)) + runid_suffix

    # FIXME: this function is confusing.  Various parts of the code need to
    #  know whether they want the csum or the stamp, when in theory, the csum
    #  should just override the stamp.
    def csum_or_read_stamp(self):
        newstamp = self.read_stamp()
        if newstamp == self.stamp:
            return self.csum or newstamp
        else:
            # old csum is meaningless because file changed after it was
            # recorded.
            return newstamp


def is_missing(stamp):
    if not stamp:
        return False
    return stamp == STAMP_MISSING or stamp.startswith(STAMP_MISSING + '+')
