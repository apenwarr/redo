"""Code for manipulating redo's state database."""
import sys, os, errno, stat, fcntl, sqlite3
from . import cycles, env
from .helpers import unlink, close_on_exec, join
from .logs import warn, debug2, debug3

SCHEMA_VER = 2
TIMEOUT = 60

ALWAYS = '//ALWAYS'   # an invalid filename that is always marked as dirty
STAMP_DIR = 'dir'     # the stamp of a directory; mtime is unhelpful
STAMP_MISSING = '0'   # the stamp of a nonexistent file

LOG_LOCK_MAGIC = 0x10000000  # fid offset for "log locks"


def _connect(dbfile):
    _db = sqlite3.connect(dbfile, timeout=TIMEOUT)
    _db.execute("pragma synchronous = off")
    # Some old/broken versions of pysqlite on MacOS work badly with journal
    # mode PERSIST.  But WAL fails on Windows WSL due to WSL's totally broken
    # locking.  On WSL, at least PERSIST works in single-threaded mode, so
    # if we're careful we can use it, more or less.
    jmode = 'PERSIST' if env.v.LOCKS_BROKEN else 'WAL'
    _db.execute("pragma journal_mode = %s" % (jmode,))
    _db.text_factory = str
    return _db


# We need to keep a process-wide fd open for all access to the lock file.
# Because POSIX lock files are insane, if you close *one* fd pointing
# at a given inode, it will immediately release *all* locks on that inode from
# your pid, even if those locks are on a different fd.  This is literally
# never what you want.  To avoid the problem, always use just a single fd.
_lockfile = None


_db = None
def db():
    """Initialize the state database and return its object."""
    global _db, _lockfile
    if _db:
        return _db

    dbdir = '%s/.redo' % env.v.BASE
    dbfile = '%s/db.sqlite3' % dbdir
    try:
        os.mkdir(dbdir)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass  # if it exists, that's okay
        else:
            raise

    _lockfile = os.open(os.path.join(env.v.BASE, '.redo/locks'),
                        os.O_RDWR | os.O_CREAT, 0666)
    close_on_exec(_lockfile, True)
    if env.is_toplevel and detect_broken_locks():
        env.mark_locks_broken()

    must_create = not os.path.exists(dbfile)
    if not must_create:
        _db = _connect(dbfile)
        try:
            row = _db.cursor().execute("select version from Schema").fetchone()
        except sqlite3.OperationalError:
            row = None
        ver = row and row[0] or None
        if ver != SCHEMA_VER:
            # Don't use err() here because this might happen before
            # redo-log spawns.
            sys.stderr.write(
                'redo: %s: found v%s (expected v%s)\n'
                % (dbfile, ver, SCHEMA_VER))
            sys.stderr.write('redo: manually delete .redo dir to start over.\n')
            sys.exit(1)
    if must_create:
        unlink(dbfile)
        _db = _connect(dbfile)
        _db.execute("create table Schema "
                    "    (version int)")
        _db.execute("create table Runid "
                    "    (id integer primary key autoincrement)")
        _db.execute("create table Files "
                    "    (name not null primary key, "
                    "     is_generated int, "
                    "     is_override int, "
                    "     checked_runid int, "
                    "     changed_runid int, "
                    "     failed_runid int, "
                    "     stamp, "
                    "     csum)")
        _db.execute("create table Deps "
                    "    (target int, "
                    "     source int, "
                    "     mode not null, "
                    "     delete_me int, "
                    "     primary key (target,source))")
        _db.execute("insert into Schema (version) values (?)", [SCHEMA_VER])
        # eat the '0' runid and File id.
        # Because of the cheesy way t/flush-cache is implemented, leave a
        # lot of runids available before the "first" one so that we
        # can adjust cached values to be before the first value.
        _db.execute("insert into Runid values (1000000000)")
        _db.execute("insert into Files (name) values (?)", [ALWAYS])

    if not env.v.RUNID:
        _db.execute("insert into Runid values "
                    "     ((select max(id)+1 from Runid))")
        env.v.RUNID = _db.execute("select last_insert_rowid()").fetchone()[0]
        os.environ['REDO_RUNID'] = str(env.v.RUNID)

    _db.commit()
    return _db


def init(targets):
    env.init(targets)
    db()
    if env.is_toplevel and detect_broken_locks():
        env.mark_locks_broken()


_wrote = 0
def _write(q, l):
    if _insane:
        return
    global _wrote
    _wrote += 1
    db().execute(q, l)


def commit():
    if _insane:
        return
    global _wrote
    if _wrote:
        db().commit()
        _wrote = 0


def rollback():
    if _insane:
        return
    global _wrote
    if _wrote:
        db().rollback()
        _wrote = 0


def is_flushed():
    return not _wrote


_insane = None
def check_sane():
    global _insane
    if not _insane:
        _insane = not os.path.exists('%s/.redo' % env.v.BASE)
    return not _insane


def _realdirpath(t):
    """Like realpath(), but don't follow symlinks for the last element.

    redo needs this because targets can be symlinks themselves, and we want
    to talk about the symlink, not what it points at.  However, all the path
    elements along the way could result in pathname aliases for a *particular*
    target, so we want to resolve it to one unique name.
    """
    dname, fname = os.path.split(t)
    if dname:
        dname = os.path.realpath(dname)
    return os.path.join(dname, fname)


_cwd = None
def relpath(t, base):
    """Given a relative or absolute path t, express it relative to base."""
    global _cwd
    if not _cwd:
        _cwd = os.getcwd()
    t = os.path.normpath(_realdirpath(os.path.join(_cwd, t)))
    base = os.path.normpath(_realdirpath(base))
    tparts = t.split('/')
    bparts = base.split('/')
    for tp, bp in zip(tparts, bparts):
        if tp != bp:
            break
        tparts.pop(0)
        bparts.pop(0)
    while bparts:
        tparts.insert(0, '..')
        bparts.pop(0)
    return join('/', tparts)


# Return a relative path for t that will work after we do
# chdir(dirname(env.v.TARGET)).
#
# This is tricky!  STARTDIR+PWD is the directory for the *dofile*, when
# the dofile was started.  However, inside the dofile, someone may have done
# a chdir to anywhere else.  env.v.TARGET is relative to the dofile path, so
# we have to first figure out where the dofile was, then find TARGET relative
# to that, then find t relative to that.
#
# FIXME: find some cleaner terminology for all these different paths.
def target_relpath(t):
    dofile_dir = os.path.abspath(os.path.join(env.v.STARTDIR, env.v.PWD))
    target_dir = os.path.abspath(
        os.path.dirname(os.path.join(dofile_dir, env.v.TARGET)))
    return relpath(t, target_dir)


def detect_override(stamp1, stamp2):
    """Determine if two stamps differ in a way that means manual override.

    When two stamps differ at all, that means the source is dirty and so we
    need to rebuild.  If they differ in mtime or size, then someone has surely
    edited the file, and we don't want to trample their changes.

    But if the only difference is something else (like ownership, st_mode,
    etc) then that might be a false positive; it's annoying to mark as
    overridden in that case, so we return False.  (It's still dirty though!)
    """
    if stamp1 == stamp2:
        return False
    crit1 = stamp1.split('-', 2)[0:2]
    crit2 = stamp2.split('-', 2)[0:2]
    return crit1 != crit2


def warn_override(name):
    warn('%s - you modified it; skipping\n' % name)


_file_cols = ['rowid', 'name', 'is_generated', 'is_override',
              'checked_runid', 'changed_runid', 'failed_runid',
              'stamp', 'csum']
class File(object):
    """An object representing a source or target in the redo database."""

    # use this mostly to avoid accidentally assigning to typos
    __slots__ = ['id'] + _file_cols[1:]

    # These warnings are a result of the weird way this class is
    # initialized, which we should fix, and then re-enable warning.
    # pylint: disable=attribute-defined-outside-init
    def _init_from_idname(self, fid, name, allow_add):
        q = ('select %s from Files ' % join(', ', _file_cols))
        if fid != None:
            q += 'where rowid=?'
            l = [fid]
        elif name != None:
            name = (name == ALWAYS) and ALWAYS or relpath(name, env.v.BASE)
            q += 'where name=?'
            l = [name]
        else:
            raise Exception('name or id must be set')
        d = db()
        row = d.execute(q, l).fetchone()
        if not row:
            if not name:
                raise KeyError('No file with id=%r name=%r' % (fid, name))
            elif not allow_add:
                raise KeyError('No file with name=%r' % (name,))
            try:
                _write('insert into Files (name) values (?)', [name])
            except sqlite3.IntegrityError:
                # some parallel redo probably added it at the same time; no
                # big deal.
                pass
            row = d.execute(q, l).fetchone()
            assert row
        return self._init_from_cols(row)

    def _init_from_cols(self, cols):
        (self.id, self.name, self.is_generated, self.is_override,
         self.checked_runid, self.changed_runid, self.failed_runid,
         self.stamp, self.csum) = cols
        if self.name == ALWAYS and self.changed_runid < env.v.RUNID:
            self.changed_runid = env.v.RUNID

    def __init__(self, fid=None, name=None, cols=None, allow_add=True):
        if cols:
            self._init_from_cols(cols)
        else:
            self._init_from_idname(fid, name, allow_add=allow_add)

    def __repr__(self):
        return "File(%r)" % (self.nicename(),)

    def refresh(self):
        self._init_from_idname(self.id, None, allow_add=False)

    def save(self):
        cols = join(', ', ['%s=?'%i for i in _file_cols[2:]])
        _write('update Files set '
               '    %s '
               '    where rowid=?' % cols,
               [self.is_generated, self.is_override,
                self.checked_runid, self.changed_runid, self.failed_runid,
                self.stamp, self.csum,
                self.id])

    def set_checked(self):
        self.checked_runid = env.v.RUNID

    def set_checked_save(self):
        self.set_checked()
        self.save()

    def set_changed(self):
        debug2('BUILT: %r (%r)\n' % (self.name, self.stamp))
        self.changed_runid = env.v.RUNID
        self.failed_runid = None
        self.is_override = False

    def set_failed(self):
        debug2('FAILED: %r\n' % self.name)
        self.update_stamp()
        self.failed_runid = env.v.RUNID
        if self.stamp != STAMP_MISSING:
            # if we failed and the target file still exists,
            # then we're generated.
            self.is_generated = True
        else:
            # if the target file now does *not* exist, then go back to
            # treating this as a source file.  Since it doesn't exist,
            # if someone tries to rebuild it immediately, it'll go
            # back to being a target.  But if the file is manually
            # created before that, we don't need a "manual override"
            # warning.
            self.is_generated = False

    def set_static(self):
        self.update_stamp(must_exist=True)
        self.failed_runid = None
        self.is_override = False
        self.is_generated = False

    def set_override(self):
        self.update_stamp()
        self.failed_runid = None
        self.is_override = True

    def update_stamp(self, must_exist=False):
        newstamp = self.read_stamp()
        if must_exist and newstamp == STAMP_MISSING:
            raise Exception("%r does not exist" % self.name)
        if newstamp != self.stamp:
            debug2("STAMP: %s: %r -> %r\n" % (self.name, self.stamp, newstamp))
            self.stamp = newstamp
            self.set_changed()

    def is_source(self):
        """Returns true if this object represents a source (not a target)."""
        if self.name.startswith('//'):
            return False  # special name, ignore
        newstamp = self.read_stamp()
        if (self.is_generated and
                (not self.is_failed() or newstamp != STAMP_MISSING) and
                not self.is_override and
                self.stamp == newstamp):
            # target is as we left it
            return False
        if ((not self.is_generated or self.stamp != newstamp) and
                newstamp == STAMP_MISSING):
            # target has gone missing after the last build.
            # It's not usefully a source *or* a target.
            return False
        return True

    def is_target(self):
        """Returns true if this object represents a target (not a source)."""
        if not self.is_generated:
            return False
        if self.is_source():
            return False
        return True

    def is_checked(self):
        return self.checked_runid and self.checked_runid >= env.v.RUNID

    def is_changed(self):
        return self.changed_runid and self.changed_runid >= env.v.RUNID

    def is_failed(self):
        return self.failed_runid and self.failed_runid >= env.v.RUNID

    def deps(self):
        """Return the list of objects that this object depends on."""
        if self.is_override or not self.is_generated:
            return
        q = ('select Deps.mode, Deps.source, %s '
             '  from Files '
             '    join Deps on Files.rowid = Deps.source '
             '  where target=?' % join(', ', _file_cols[1:]))
        for row in db().execute(q, [self.id]).fetchall():
            mode = row[0]
            cols = row[1:]
            assert mode in ('c', 'm')
            yield mode, File(cols=cols)

    def zap_deps1(self):
        """Mark the list of dependencies of this object as deprecated.

        We do this when starting a new build of the current target.  We don't
        delete them right away, because if the build fails, we still want to
        know the old deps.
        """
        debug2('zap-deps1: %r\n' % self.name)
        _write('update Deps set delete_me=? where target=?', [True, self.id])

    def zap_deps2(self):
        """Delete any deps that were *not* referenced in the current run.

        Dependencies of a given target can change from one build to the next.
        We forget old dependencies only after a build completes successfully.
        """
        debug2('zap-deps2: %r\n' % self.name)
        _write('delete from Deps where target=? and delete_me=1', [self.id])

    def add_dep(self, mode, dep):
        src = File(name=dep)
        debug3('add-dep: "%s" < %s "%s"\n' % (self.name, mode, src.name))
        assert self.id != src.id
        _write("insert or replace into Deps "
               "    (target, mode, source, delete_me) values (?,?,?,?)",
               [self.id, mode, src.id, False])

    def _read_stamp_st(self, statfunc):
        try:
            st = statfunc(os.path.join(env.v.BASE, self.name))
        except OSError:
            return False, STAMP_MISSING
        if stat.S_ISDIR(st.st_mode):
            # directories change too much; detect only existence.
            return False, STAMP_DIR
        else:
            # a "unique identifier" stamp for a regular file
            return (
                stat.S_ISLNK(st.st_mode),
                '-'.join(str(s) for s in
                         ('%.6f' % st.st_mtime, st.st_size, st.st_ino,
                          st.st_mode, st.st_uid, st.st_gid))
            )

    def read_stamp(self):
        is_link, pre = self._read_stamp_st(os.lstat)
        if is_link:
            # if we're a symlink, we actually care about the link object
            # itself, *and* the target of the link.  If either changes,
            # we're considered dirty.
            #
            # On the other hand, detect_override() doesn't care about the
            # target of the link, only the link itself.
            _, post = self._read_stamp_st(os.stat)
            return pre + '+' + post
        else:
            return pre

    def nicename(self):
        return relpath(os.path.join(env.v.BASE, self.name), env.v.STARTDIR)


def files():
    q = ('select %s from Files order by name' % join(', ', _file_cols))
    for cols in db().execute(q).fetchall():
        yield File(cols=cols)


def logname(fid):
    """Given the id of a File, return the filename of its build log."""
    return os.path.join(env.v.BASE, '.redo', 'log.%d' % fid)


# FIXME: I really want to use fcntl F_SETLK, F_SETLKW, etc here.  But python
# doesn't do the lockdata structure in a portable way, so we have to use
# fcntl.lockf() instead.  Usually this is just a wrapper for fcntl, so it's
# ok, but it doesn't have F_GETLK, so we can't report which pid owns the lock.
# The makes debugging a bit harder.  When we someday port to C, we can do that.
_locks = {}
class Lock(object):
    """An object representing a lock on a redo target file."""

    def __init__(self, fid):
        """Initialize a lock, given the target's state.File.id."""
        self.owned = False
        self.fid = fid
        assert _lockfile >= 0
        assert _locks.get(fid, 0) == 0
        _locks[fid] = 1

    def __del__(self):
        _locks[self.fid] = 0
        if self.owned:
            self.unlock()

    def check(self):
        """Check that this lock is in a sane state."""
        assert not self.owned
        cycles.check(self.fid)

    def trylock(self):
        """Non-blocking try to acquire our lock; returns true if it worked."""
        self.check()
        assert not self.owned
        try:
            fcntl.lockf(_lockfile, fcntl.LOCK_EX|fcntl.LOCK_NB, 1, self.fid)
        except IOError, e:
            if e.errno in (errno.EAGAIN, errno.EACCES):
                pass  # someone else has it locked
            else:
                raise
        else:
            self.owned = True
        return self.owned

    def waitlock(self, shared=False):
        """Try to acquire our lock, and wait if it's currently locked.

        If shared=True, acquires a shared lock (which can be shared with
        other shared locks; used by redo-log).  Otherwise, acquires an
        exclusive lock.
        """
        self.check()
        assert not self.owned
        fcntl.lockf(
            _lockfile,
            fcntl.LOCK_SH if shared else fcntl.LOCK_EX,
            1, self.fid)
        self.owned = True

    def unlock(self):
        """Release the lock, which we must currently own."""
        if not self.owned:
            raise Exception("can't unlock %r - we don't own it"
                            % self.fid)
        fcntl.lockf(_lockfile, fcntl.LOCK_UN, 1, self.fid)
        self.owned = False


def detect_broken_locks():
    """Detect Windows WSL's completely broken fcntl() locks.

    Symptom: locking a file always returns success, even if other processes
    also think they have it locked. See
    https://github.com/Microsoft/WSL/issues/1927 for more details.

    Bug exists at least in WSL "4.4.0-17134-Microsoft #471-Microsoft".

    Returns true if broken, false otherwise.
    """
    pl = Lock(0)
    # We wait for the lock here, just in case others are doing
    # this test at the same time.
    pl.waitlock(shared=False)
    pid = os.fork()
    if pid:
        # parent
        _, rv = os.waitpid(pid, 0)
        ok = os.WIFEXITED(rv) and not os.WEXITSTATUS(rv)
        return not ok
    else:
        # child
        try:
            # Doesn't actually unlock, since child process doesn't own it
            pl.unlock()
            del pl
            cl = Lock(0)
            # parent is holding lock, which should prevent us from getting it.
            owned = cl.trylock()
            if owned:
                # Got the lock? Yikes, the locking system is broken!
                os._exit(1)
            else:
                # Failed to get the lock? Good, the parent owns it.
                os._exit(0)
        except Exception:  # pylint: disable=broad-except
            import traceback
            traceback.print_exc()
        finally:
            os._exit(99)
