import sys, os, errno, stat
import vars, state, jwack, deps
from helpers import unlink, close_on_exec, join
from log import log, log_, debug, debug2, debug3, err, warn


def _default_do_files(filename):
    l = filename.split('.')
    for i in range(1,len(l)+1):
        basename = join('.', l[:i])
        ext = join('.', l[i:])
        if ext: ext = '.' + ext
        yield ("default%s.do" % ext), basename, ext
    

def _possible_do_files(t):
    dirname,filename = os.path.split(t)
    yield (dirname, "%s.do" % filename, '', filename, '')

    # It's important to try every possibility in a directory before resorting
    # to a parent directory.  Think about nested projects: I don't want
    # ../../default.o.do to take precedence over ../default.do, because
    # the former one might just be an artifact of someone embedding my project
    # into theirs as a subdir.  When they do, my rules should still be used
    # for building my project in *all* cases.
    dirname,filename = os.path.split(t)
    dirbits = os.path.abspath(dirname).split('/')
    for i in range(len(dirbits), -1, -1):
        basedir = os.path.join(dirname,
                               join('/', ['..'] * (len(dirbits) - i)))
        subdir = join('/', dirbits[i:])
        for dofile,basename,ext in _default_do_files(filename):
            yield (basedir, dofile,
                   subdir, os.path.join(subdir, basename), ext)
        

def _find_do_file(f):
    for dodir,dofile,basedir,basename,ext in _possible_do_files(f.name):
        if dodir and not os.path.isdir(dodir):
            # we don't want to normpath() unless we have no other choice.
            # otherwise we could have odd behaviour with symlinks (ie.
            # x/y/../z might not be the same as x/z).  On the other hand,
            # if one of the path elements doesn't exist (yet), normpath
            # can help us find the .do file anyway, and that .do file might
            # create the sub-path.
            dodir = os.path.normpath(dodir)
        dopath = os.path.join(dodir, dofile)
        debug2('%s: %s:%s ?\n', f.name, dodir, dofile)
        dof = state.File(dopath)
        if os.path.exists(dopath):
            f.add_dep(dof)
            return dodir,dofile,basedir,basename,ext
        else:
            f.add_dep(dof)
    return None,None,None,None,None


def _try_stat(filename):
    try:
        return os.stat(filename)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return None
        else:
            raise

class BuildJob:
    def __init__(self, target, result):
        self.target = target
        self.result = result

    def build(self):
        target = self.target
        debug3('thinking about building %r\n', target.name)
        target.build_starting()
        before_t = _try_stat(target.name)

        newstamp = target.read_stamp()
        if target.is_generated and newstamp != target.stamp:
            if state.is_missing(newstamp):
                # was marked generated, but is now deleted
                debug3('oldstamp=%r newstamp=%r\n', target.stamp, newstamp)
                target.forget()
                target.refresh()
            elif vars.OVERWRITE:
                warn('%s: you modified it; overwrite\n', target.printable_name())
            else:
                warn('%s: you modified it; skipping\n', target.printable_name())
                return 0
        if (os.path.exists(target.name) and
            not os.path.isdir(target.name) and
            not target.is_generated):
            # an existing source file that was not generated by us.
            # This step is mentioned by djb in his notes.
            # For example, a rule called default.c.do could be used to try
            # to produce hello.c, but we don't want that to happen if
            # hello.c was created in advance by the end user.
            if vars.OVERWRITE:
                warn('%s: exists and not marked as generated; overwrite.\n',
                     target.printable_name())
            else:
                warn('%s: exists and not marked as generated; not redoing.\n',
                     target.printable_name())
                debug2('-- static (%r)\n', target.name)
                return 0
        (dodir, dofile, basedir, basename, ext) = _find_do_file(target)
        if not dofile:
            if state.is_missing(newstamp):
                err('no rule to make %r\n', target.name)
                return 1
            else:
                target.forget()
                return 0  # no longer a generated target, but exists, so ok

        tmpname1 = target.tmpfilename('redo1.tmp')  # name connected to stdout
        tmpname2 = target.tmpfilename('redo2.tmp')  # name provided as $3
        unlink(tmpname1)
        unlink(tmpname2)
        tmp1_fd = os.open(tmpname1, os.O_CREAT|os.O_RDWR|os.O_EXCL, 0666)
        close_on_exec(tmp1_fd, True)
        tmp1_f = os.fdopen(tmp1_fd, 'w+')

        # this will run in the dofile's directory, so use only basenames here
        if vars.OLD_ARGS:
            arg1 = basename  # target name (no extension)
            arg2 = ext       # extension (if any), including leading dot
        else:
            arg1 = basename + ext  # target name (including extension)
            arg2 = basename        # target name (without extension)
        argv = ['sh', '-e',
                dofile,
                arg1,
                arg2,
                # temp output file name
                os.path.relpath(tmpname2, dodir),
                ]
        if vars.VERBOSE: argv[1] += 'v'
        if vars.XTRACE: argv[1] += 'x'
        if vars.VERBOSE or vars.XTRACE: log_('\n')
        firstline = open(os.path.join(dodir, dofile)).readline().strip()
        if firstline.startswith('#!/'):
            argv[0:2] = firstline[2:].split(' ')
        log('%s\n', target.printable_name())

        pid = os.fork()
        if pid == 0:  # child
            try:
                dn = dodir
                os.environ['REDO_PWD'] = os.path.join(vars.PWD, dn)
                os.environ['REDO_TARGET'] = basename + ext
                os.environ['REDO_DEPTH'] = vars.DEPTH + '  '
                if dn:
                    os.chdir(dn)
                os.dup2(tmp1_f.fileno(), 1)
                os.close(tmp1_f.fileno())
                close_on_exec(1, False)
                if vars.VERBOSE or vars.XTRACE: log_('* %s\n' % ' '.join(argv))
                os.execvp(argv[0], argv)
            except:
                import traceback
                sys.stderr.write(traceback.format_exc())
                err('internal exception - see above\n')
                raise
            finally:
                # returns only if there's an exception
                os._exit(127)

        # otherwise, we're the parent
        outpid, status = 0, -42
        while outpid != pid:
            outpid, status = os.waitpid(pid, 0)
        if os.WIFEXITED(status):
            rv = os.WEXITSTATUS(status)
        else:
            rv = -os.WSTOPSIG(status)

        after_t = _try_stat(target.name)
        st1 = os.fstat(tmp1_f.fileno())
        st2 = _try_stat(tmpname2)
        if (after_t and 
            (not before_t or before_t.st_ctime != after_t.st_ctime) and
            not stat.S_ISDIR(after_t.st_mode)):
                err('%s modified %s directly!\n', argv[2], target.name)
                err('...you should update $3 (a temp file) or stdout, not $1.\n')
                rv = 206
        elif st2 and st1.st_size > 0:
            err('%s wrote to stdout *and* created $3.\n', argv[2])
            err('...you should write status messages to stderr, not stdout.\n')
            rv = 207
        if rv==0:
            if st2:
                os.rename(tmpname2, target.name)
                os.unlink(tmpname1)
            elif st1.st_size > 0:
                try:
                    os.rename(tmpname1, target.name)
                except OSError, e:
                    if e.errno == errno.ENOENT:
                        unlink(target.name)
                    else:
                        raise
            else: # no output generated at all; that's ok
                unlink(tmpname1)
                unlink(target.name)
            if vars.VERBOSE or vars.XTRACE or vars.DEBUG:
                log('%s (done)\n\n', target.printable_name())
        else:
            unlink(tmpname1)
            unlink(tmpname2)
        target.build_done(exitcode=rv)
        tmp1_f.close()
        if rv != 0:
            err('%s: exit code %d\n', target.printable_name(), rv)
        return rv

    def done(self, t, rv):
        assert self.target.dolock.owned == state.LOCK_EX
        try:
            self.result[0] += rv
            self.result[1] += 1
        finally:
            self.target.dolock.unlock()
    
    def prepare(self):
        assert self.target.dolock.owned == state.LOCK_EX
        # Do everything that requires a lock
        # self.build must not require the lock at all
        pass
    
    def schedule_job(self):
        assert self.target.dolock.owned == state.LOCK_EX
        self.prepare()
        jwack.start_job(self.target, self.build, self.done)

def build(f, any_errors, should_build):
    dirty = should_build(f)
    while dirty and dirty != deps.DIRTY:
        # FIXME: bring back the old (targetname) notation in the output
        #  when we need to do this.  And add comments.
        for t2 in dirty:
            build(t2, any_errors, should_build)
            if any_errors[0] and not vars.KEEP_GOING:
                return
        dirty = should_build(f)
        #assert(dirty in (deps.DIRTY, deps.CLEAN))
    if dirty:
        job = BuildJob(f, any_errors)
        f.dolock.waitlock()
        job.schedule_job()
        jwack.wait_all() # temp: wait for the job to complete

def main(targets, should_build = (lambda f: deps.DIRTY), parent = None):
    any_errors = [0, 0]
    if vars.SHUFFLE:
        import random
        random.shuffle(targets)

    try:
        for t in targets:
            f = state.File(name=t)
            if parent:
                f.refresh()
                parent.add_dep(f)
            build(f, any_errors, should_build)
            if any_errors[0] and not vars.KEEP_GOING:
                break
    finally:
        jwack.force_return_tokens()

    if any_errors[1] == 1:
        return any_errors[0]
    elif any_errors[0]:
        return 1
    else:
        return 0

