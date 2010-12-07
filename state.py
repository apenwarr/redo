import sys, os, errno, glob, stat, sqlite3
import vars
from helpers import unlink, err, debug2, debug3, mkdirp, close_on_exec

SCHEMA_VER=7

_db = None
def db():
    global _db
    if _db:
        return _db
    dbdir = '%s/.redo' % vars.BASE
    dbfile = '%s/db.sqlite3' % dbdir
    mkdirp(dbdir)
    must_create = not os.path.exists(dbfile)
    if not must_create:
        _db = sqlite3.connect(dbfile)
        try:
            row = _db.cursor().execute("select version from Schema").fetchone()
        except sqlite3.OperationalError:
            row = None
        ver = row and row[0] or None
        if ver != SCHEMA_VER:
            err("state database: discarding v%s (wanted v%s)\n"
                % (ver, SCHEMA_VER))
            must_create = True
            _db = None
    if must_create:
        unlink(dbfile)
        _db = sqlite3.connect(dbfile)
        _db.execute("create table Schema (version int)")
        _db.execute("create table Runid "
                    "    (id integer primary key autoincrement)")
        _db.execute("create table Files ("
                    "    name not null primary key, "
                    "    is_generated int, "
                    "    checked_runid int, "
                    "    changed_runid int, "
                    "    stamp, csum)")
        _db.execute("create table Deps "
                    "    (target int, source int, mode not null, primary key (target,source))")
        #_db.execute("create unique index Files_name on Files (name)")
        #_db.execute("create unique index Deps_ix on Deps (target, source)")
        _db.execute("create index Deps_src on Deps (source)")
        _db.execute("insert into Schema (version) values (?)", [SCHEMA_VER])
        _db.execute("insert into Runid default values")
        _db.execute("insert into Runid default values")
        _db.commit()

    if not vars.RUNID:
        _db.execute("insert into Runid default values")
        _db.commit()
        vars.RUNID = _db.execute("select last_insert_rowid()").fetchone()[0]
        os.environ['REDO_RUNID'] = str(vars.RUNID)
    
    _db.execute("pragma journal_mode = PERSIST")
    _db.execute("pragma synchronous = off")
    return _db
    

def init():
    # FIXME: just wiping out all the locks is kind of cheating.  But we
    # only do this from the toplevel redo process, so unless the user
    # deliberately starts more than one redo on the same repository, it's
    # sort of ok.
    db()
    for f in glob.glob('%s/.redo/lock*' % vars.BASE):
        os.unlink(f)


_insane = None
def is_sane():
    global _insane
    if not _insane:
        _insane = not os.path.exists('%s/.redo' % vars.BASE)
        if _insane:
            err('.redo directory disappeared; cannot continue.\n')
    return not _insane


_cwd = None
def relpath(t, base):
    global _cwd
    if not _cwd:
        _cwd = os.getcwd()
    t = os.path.normpath(os.path.join(_cwd, t))
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
    return '/'.join(tparts)


def xx_sname(typ, t):
    # FIXME: t.replace(...) is non-reversible and non-unique here!
    tnew = relpath(t, vars.BASE)
    v = vars.BASE + ('/.redo/%s^%s' % (typ, tnew.replace('/', '^')))
    if vars.DEBUG >= 3:
        debug3('sname: (%r) %r -> %r\n' % (os.getcwd(), t, tnew))
    return v


class File(object):
    __slots__ = ['id', 'name', 'is_generated',
                 'checked_runid', 'changed_runid',
                 'stamp', 'csum']
    
    def __init__(self, id=None, name=None):
        q = ('select rowid, name, is_generated, checked_runid, changed_runid, '
             '    stamp, csum '
             '  from Files ')
        if id != None:
            q += 'where rowid=?'
            l = [id]
        elif name != None:
            name = relpath(name, vars.BASE)
            q += 'where name=?'
            l = [name]
        else:
            raise Exception('name or id must be set')
        d = db()
        row = d.execute(q, l).fetchone()
        if not row:
            if not name:
                raise Exception('File with id=%r not found and '
                                'name not given' % id)
            d.execute('insert into Files (name) values (?)', [name])
            d.commit()
            row = d.execute(q, l).fetchone()
            assert(row)
        (self.id, self.name, self.is_generated,
         self.checked_runid, self.changed_runid,
         self.stamp, self.csum) = row

    def save(self):
        if not os.path.exists('%s/.redo' % vars.BASE):
            # this might happen if 'make clean' removes the .redo dir
            return
        d = db()
        d.execute('update Files set '
                  '    is_generated=?, checked_runid=?, changed_runid=?, '
                  '    stamp=?, csum=? '
                  '    where rowid=?',
                  [self.is_generated, self.checked_runid, self.changed_runid,
                   self.stamp, self.csum,
                   self.id])
        d.commit()

    def set_checked(self):
        self.checked_runid = vars.RUNID
        
    def set_changed(self):
        debug2('BUILT: %r (%r)\n' % (self.name, self.stamp))
        self.changed_runid = vars.RUNID

    def set_static(self):
        self.update_stamp()

    def update_stamp(self):
        newstamp = self.read_stamp()
        if newstamp != self.stamp:
            debug2("STAMP: %s: %r -> %r\n" % (self.name, self.stamp, newstamp))
            self.stamp = newstamp
            self.set_changed()

    def is_changed(self):
        return self.changed_runid and self.changed_runid >= vars.RUNID

    def is_checked(self):
        return (self.checked_runid and self.checked_runid >= vars.RUNID
                and not (self.changed_runid 
                         and self.changed_runid >= self.checked_runid))

    def deps(self):
        q = "select mode, source from Deps where target=?"
        for mode,source_id in db().execute(q, [self.id]):
            assert(mode in ('c', 'm'))
            name = File(id=source_id).name
            yield mode,name

    def zap_deps(self):
        debug2('zap-deps: %r\n' % self.name)
        db().execute('delete from Deps where target=?', [self.id])
        db().commit()

    def add_dep(self, mode, dep):
        src = File(name=dep)
        reldep = relpath(dep, vars.BASE)
        debug2('add-dep: %r < %s %r\n' % (self.name, mode, reldep))
        assert(src.name == reldep)
        d = db()
        d.execute("delete from Deps where target=? and source=?",
                  [self.id, src.id])
        d.execute("insert into Deps "
                  "    (target, mode, source) values (?,?,?)",
                  [self.id, mode, src.id])
        d.commit()

    def read_stamp(self):
        try:
            st = os.stat(os.path.join(vars.BASE, self.name))
        except OSError:
            return '0'  # does not exist
        if stat.S_ISDIR(st.st_mode):
            return 'dir'  # the timestamp of a directory is meaningless
        else:
            # a "unique identifier" stamp for a regular file
            return str((st.st_ctime, st.st_mtime, st.st_size, st.st_ino))
        


class Lock:
    def __init__(self, t):
        self.owned = False
        self.rfd = self.wfd = None
        self.lockname = xx_sname('lock', t)

    def __del__(self):
        if self.owned:
            self.unlock()

    def trylock(self):
        try:
            os.mkfifo(self.lockname, 0600)
            self.owned = True
            self.rfd = os.open(self.lockname, os.O_RDONLY|os.O_NONBLOCK)
            self.wfd = os.open(self.lockname, os.O_WRONLY)
            close_on_exec(self.rfd, True)
            close_on_exec(self.wfd, True)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

    def waitlock(self):
        while not self.owned:
            self.wait()
            self.trylock()
        assert(self.owned)
            
    def unlock(self):
        if not self.owned:
            raise Exception("can't unlock %r - we don't own it" 
                            % self.lockname)
        unlink(self.lockname)
        # ping any connected readers
        os.close(self.rfd)
        os.close(self.wfd)
        self.rfd = self.wfd = None
        self.owned = False

    def wait(self):
        if self.owned:
            raise Exception("can't wait on %r - we own it" % self.lockname)
        try:
            # open() will finish only when a writer exists and does close()
            fd = os.open(self.lockname, os.O_RDONLY)
            try:
                os.read(fd, 1)
            finally:
                os.close(fd)
        except OSError, e:
            if e.errno == errno.ENOENT:
                pass  # it's not even unlocked or was unlocked earlier
            else:
                raise
