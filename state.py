import sys, os, errno, glob, stat, fcntl, sqlite3
import vars
from helpers import unlink, close_on_exec, join
from logs import warn, err, debug2, debug3

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

SCHEMA_VER=2
TIMEOUT=60

ALWAYS='//ALWAYS'   # an invalid filename that is always marked as dirty
STAMP_DIR='dir'     # the stamp of a directory; mtime is unhelpful
STAMP_MISSING='0'   # the stamp of a nonexistent file

LOG_LOCK_MAGIC=0x10000000  # fid offset for "log locks"


class CyclicDependencyError(Exception): pass


def _connect(dbfile):
    _db = sqlite3.connect(dbfile, timeout=TIMEOUT)
    _db.execute("pragma synchronous = off")
    _db.execute("pragma journal_mode = WAL")
    _db.text_factory = str
    return _db


_db = None
def db():
    global _db
    if _db:
        return _db
        
    dbdir = '%s/.redo' % vars.BASE
    dbfile = '%s/db.sqlite3' % dbdir
    try:
        os.mkdir(dbdir)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass  # if it exists, that's okay
        else:
            raise

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
            sys.stderr.write('redo: %s: found v%s (expected v%s)\n'
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
        # eat the '0' runid and File id
        _db.execute("insert into Runid values "
                    "     ((select max(id)+1 from Runid))")
        _db.execute("insert into Files (name) values (?)", [ALWAYS])

    if not vars.RUNID:
        _db.execute("insert into Runid values "
                    "     ((select max(id)+1 from Runid))")
        vars.RUNID = _db.execute("select last_insert_rowid()").fetchone()[0]
        os.environ['REDO_RUNID'] = str(vars.RUNID)
    
    _db.commit()
    return _db
    

def init():
    db()


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
    global _insane, _writable
    if not _insane:
        _insane = not os.path.exists('%s/.redo' % vars.BASE)
    return not _insane


_cwd = None
def relpath(t, base):
    global _cwd
    if not _cwd:
        _cwd = os.getcwd()
    t = os.path.normpath(os.path.join(_cwd, t))
    base = os.path.normpath(base)
    tparts = t.split('/')
    bparts = base.split('/')
    for tp,bp in zip(tparts,bparts):
        if tp != bp:
            break
        tparts.pop(0)
        bparts.pop(0)
    while bparts:
        tparts.insert(0, '..')
        bparts.pop(0)
    return join('/', tparts)


# Return a path for t, if cwd were the dirname of vars.TARGET.
# This is tricky!  STARTDIR+PWD is the directory for the *dofile*, when
# the dofile was started.  However, inside the dofile, someone may have done
# a chdir to anywhere else.  vars.TARGET is relative to the dofile path, so
# we have to first figure out where the dofile was, then find TARGET relative
# to that, then find t relative to that.
#
# FIXME: find some cleaner terminology for all these different paths.
def target_relpath(t):
    dofile_dir = os.path.abspath(os.path.join(vars.STARTDIR, vars.PWD))
    target_dir = os.path.abspath(
        os.path.dirname(os.path.join(dofile_dir, vars.TARGET)))
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
    # use this mostly to avoid accidentally assigning to typos
    __slots__ = ['id'] + _file_cols[1:]

    def _init_from_idname(self, id, name, allow_add):
        q = ('select %s from Files ' % join(', ', _file_cols))
        if id != None:
            q += 'where rowid=?'
            l = [id]
        elif name != None:
            name = (name==ALWAYS) and ALWAYS or relpath(name, vars.BASE)
            q += 'where name=?'
            l = [name]
        else:
            raise Exception('name or id must be set')
        d = db()
        row = d.execute(q, l).fetchone()
        if not row:
            if not name:
                raise KeyError('No file with id=%r name=%r' % (id, name))
            elif not allow_add:
                raise KeyError('No file with name=%r' % (name,))
            try:
                _write('insert into Files (name) values (?)', [name])
            except sqlite3.IntegrityError:
                # some parallel redo probably added it at the same time; no
                # big deal.
                pass
            row = d.execute(q, l).fetchone()
            assert(row)
        return self._init_from_cols(row)

    def _init_from_cols(self, cols):
        (self.id, self.name, self.is_generated, self.is_override,
         self.checked_runid, self.changed_runid, self.failed_runid,
         self.stamp, self.csum) = cols
        if self.name == ALWAYS and self.changed_runid < vars.RUNID:
            self.changed_runid = vars.RUNID
    
    def __init__(self, id=None, name=None, cols=None, allow_add=True):
        if cols:
            return self._init_from_cols(cols)
        else:
            return self._init_from_idname(id, name, allow_add=allow_add)

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
        self.checked_runid = vars.RUNID

    def set_checked_save(self):
        self.set_checked()
        self.save()

    def set_changed(self):
        debug2('BUILT: %r (%r)\n' % (self.name, self.stamp))
        self.changed_runid = vars.RUNID
        self.failed_runid = None
        self.is_override = False

    def set_failed(self):
        debug2('FAILED: %r\n' % self.name)
        self.update_stamp()
        self.failed_runid = vars.RUNID
        self.is_generated = True

    def set_static(self):
        self.update_stamp(must_exist=True)
        self.is_override = False
        self.is_generated = False

    def set_override(self):
        self.update_stamp()
        self.is_override = True

    def update_stamp(self, must_exist=False):
        newstamp = self.read_stamp()
        if must_exist and newstamp == STAMP_MISSING:
            raise Exception("%r does not exist" % self.name)
        if newstamp != self.stamp:
            debug2("STAMP: %s: %r -> %r\n" % (self.name, self.stamp, newstamp))
            self.stamp = newstamp
            self.set_changed()

    def is_checked(self):
        return self.checked_runid and self.checked_runid >= vars.RUNID

    def is_changed(self):
        return self.changed_runid and self.changed_runid >= vars.RUNID

    def is_failed(self):
        return self.failed_runid and self.failed_runid >= vars.RUNID

    def deps(self):
        q = ('select Deps.mode, Deps.source, %s '
             '  from Files '
             '    join Deps on Files.rowid = Deps.source '
             '  where target=?' % join(', ', _file_cols[1:]))
        for row in db().execute(q, [self.id]).fetchall():
            mode = row[0]
            cols = row[1:]
            assert(mode in ('c', 'm'))
            yield mode,File(cols=cols)

    def zap_deps1(self):
        debug2('zap-deps1: %r\n' % self.name)
        _write('update Deps set delete_me=? where target=?', [True, self.id])

    def zap_deps2(self):
        debug2('zap-deps2: %r\n' % self.name)
        _write('delete from Deps where target=? and delete_me=1', [self.id])

    def add_dep(self, mode, dep):
        src = File(name=dep)
        debug3('add-dep: "%s" < %s "%s"\n' % (self.name, mode, src.name))
        assert(self.id != src.id)
        _write("insert or replace into Deps "
               "    (target, mode, source, delete_me) values (?,?,?,?)",
               [self.id, mode, src.id, False])

    def _read_stamp_st(self, statfunc):
        try:
            st = statfunc(os.path.join(vars.BASE, self.name))
        except OSError:
            return False, STAMP_MISSING
        if stat.S_ISDIR(st.st_mode):
            # directories change too much; detect only existence.
            return False, STAMP_DIR
        else:
            # a "unique identifier" stamp for a regular file
            return (stat.S_ISLNK(st.st_mode),
                '-'.join(str(s) for s in
                         ('%.6f' % st.st_mtime, st.st_size, st.st_ino,
                          st.st_mode, st.st_uid, st.st_gid)))

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
        return relpath(os.path.join(vars.BASE, self.name), vars.STARTDIR)


def files():
    q = ('select %s from Files order by name' % join(', ', _file_cols))
    for cols in db().execute(q).fetchall():
        yield File(cols=cols)


def logname(fid):
    """Given the id of a File, return the filename of its build log."""
    return os.path.join(vars.BASE, '.redo', 'log.%d' % fid)


# FIXME: I really want to use fcntl F_SETLK, F_SETLKW, etc here.  But python
# doesn't do the lockdata structure in a portable way, so we have to use
# fcntl.lockf() instead.  Usually this is just a wrapper for fcntl, so it's
# ok, but it doesn't have F_GETLK, so we can't report which pid owns the lock.
# The makes debugging a bit harder.  When we someday port to C, we can do that.
_locks = {}
class Lock:
    def __init__(self, fid):
        self.owned = False
        self.fid = fid
        self.lockfile = None
        self.lockfile = os.open(os.path.join(vars.BASE, '.redo/lock.%d' % fid),
                                os.O_RDWR | os.O_CREAT, 0666)
        close_on_exec(self.lockfile, True)
        assert(_locks.get(fid,0) == 0)
        _locks[fid] = 1

    def __del__(self):
        _locks[self.fid] = 0
        if self.owned:
            self.unlock()
        if self.lockfile is not None:
            os.close(self.lockfile)

    def check(self):
        assert(not self.owned)
        if str(self.fid) in vars.get_locks():
            # Lock already held by parent: cyclic dependence
            raise CyclicDependencyError()

    def trylock(self):
        self.check()
        try:
            fcntl.lockf(self.lockfile, fcntl.LOCK_EX|fcntl.LOCK_NB, 0, 0)
        except IOError, e:
            if e.errno in (errno.EAGAIN, errno.EACCES):
                pass  # someone else has it locked
            else:
                raise
        else:
            self.owned = True
        return self.owned

    def waitlock(self, shared=False):
        self.check()
        fcntl.lockf(self.lockfile,
            fcntl.LOCK_SH if shared else fcntl.LOCK_EX,
            0, 0)
        self.owned = True
            
    def unlock(self):
        if not self.owned:
            raise Exception("can't unlock %r - we don't own it" 
                            % self.lockname)
        fcntl.lockf(self.lockfile, fcntl.LOCK_UN, 0, 0)
        self.owned = False
