import sys, os, errno, random, stat, signal, time
import vars, jwack, state, paths
from helpers import unlink, close_on_exec, join
import logs
from logs import debug, debug2, err, warn, meta, check_tty


def _nice(t):
    return state.relpath(t, vars.STARTDIR)


def _try_stat(filename):
    try:
        return os.lstat(filename)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return None
        else:
            raise


log_reader_pid = None


def start_stdin_log_reader(status, details, pretty, color,
                           debug_locks, debug_pids):
    if not vars.LOG: return
    global log_reader_pid
    r, w = os.pipe()    # main pipe to redo-log
    ar, aw = os.pipe()  # ack pipe from redo-log --ack-fd
    sys.stdout.flush()
    sys.stderr.flush()
    pid = os.fork()
    if pid:
        # parent
        log_reader_pid = pid
        os.close(r)
        os.close(aw)
        b = os.read(ar, 8)
        if not b:
            # subprocess died without sending us anything: that's bad.
            err('failed to start redo-log subprocess; cannot continue.\n')
            os._exit(99)
        assert b == 'REDO-OK\n'
        # now we know the subproc is running and will report our errors
        # to stderr, so it's okay to lose our own stderr.
        os.close(ar)
        os.dup2(w, 1)
        os.dup2(w, 2)
        os.close(w)
        check_tty(sys.stderr, vars.COLOR)
    else:
        # child
        try:
            os.close(ar)
            os.close(w)
            os.dup2(r, 0)
            os.close(r)
            # redo-log sends to stdout (because if you ask for logs, that's
            # the output you wanted!).  But redo itself sends logs to stderr
            # (because they're incidental to the thing you asked for).
            # To make these semantics work, we point redo-log's stdout at
            # our stderr when we launch it.
            os.dup2(2, 1)
            argv = [
                'redo-log',
                '--recursive', '--follow',
                '--ack-fd', str(aw),
                ('--status' if status and os.isatty(2) else '--no-status'),
                ('--details' if details else '--no-details'),
                ('--pretty' if pretty else '--no-pretty'),
                ('--debug-locks' if debug_locks else '--no-debug-locks'),
                ('--debug-pids' if debug_pids else '--no-debug-pids'),
            ]
            if color != 1:
                argv.append('--color' if color >= 2 else '--no-color')
            argv.append('-')
            os.execvp(argv[0], argv)
        except Exception, e:
            sys.stderr.write('redo-log: exec: %s\n' % e)
        finally:
            os._exit(99)


def await_log_reader():
    if not vars.LOG: return
    global log_reader_pid
    if log_reader_pid > 0:
        # never actually close fd#1 or fd#2; insanity awaits.
        # replace it with something else instead.
        # Since our stdout/stderr are attached to redo-log's stdin,
        # this will notify redo-log that it's time to die (after it finishes
        # reading the logs)
        out = open('/dev/tty', 'w')
        os.dup2(out.fileno(), 1)
        os.dup2(out.fileno(), 2)
        os.waitpid(log_reader_pid, 0)


class ImmediateReturn(Exception):
    def __init__(self, rv):
        Exception.__init__(self, "immediate return with exit code %d" % rv)
        self.rv = rv


class BuildJob:
    def __init__(self, t, sf, lock, shouldbuildfunc, donefunc):
        self.t = t  # original target name, not relative to vars.BASE
        self.sf = sf
        tmpbase = t
        while not os.path.isdir(os.path.dirname(tmpbase) or '.'):
            ofs = tmpbase.rfind('/')
            assert(ofs >= 0)
            tmpbase = tmpbase[:ofs] + '__' + tmpbase[ofs+1:]
        self.tmpname1 = '%s.redo1.tmp' % tmpbase
        self.tmpname2 = '%s.redo2.tmp' % tmpbase
        self.lock = lock
        self.shouldbuildfunc = shouldbuildfunc
        self.donefunc = donefunc
        self.before_t = _try_stat(self.t)

    def start(self):
        assert(self.lock.owned)
        try:
            try:
                is_target, dirty = self.shouldbuildfunc(self.t)
            except state.CyclicDependencyError:
                err('cyclic dependency while checking %s\n' % _nice(self.t))
                raise ImmediateReturn(208)
            if not dirty:
                # target doesn't need to be built; skip the whole task
                if is_target:
                    meta('unchanged', state.target_relpath(self.t))
                return self._after2(0)
        except ImmediateReturn, e:
            return self._after2(e.rv)

        if vars.NO_OOB or dirty == True:
            self._start_do()
        else:
            self._start_unlocked(dirty)

    def _start_do(self):
        assert(self.lock.owned)
        t = self.t
        sf = self.sf
        newstamp = sf.read_stamp()
        if (sf.is_generated and
            newstamp != state.STAMP_MISSING and 
            (sf.stamp != newstamp or sf.is_override)):
                state.warn_override(_nice(t))
                if not sf.is_override:
                    warn('%s - old: %r\n' % (_nice(t), sf.stamp))
                    warn('%s - new: %r\n' % (_nice(t), newstamp))
                    sf.set_override()
                sf.set_checked()
                sf.save()
                return self._after2(0)
        if (os.path.exists(t) and not os.path.isdir(t + '/.')
             and not sf.is_generated):
            # an existing source file that was not generated by us.
            # This step is mentioned by djb in his notes.
            # For example, a rule called default.c.do could be used to try
            # to produce hello.c, but we don't want that to happen if
            # hello.c was created by the end user.
            debug2("-- static (%r)\n" % t)
            sf.set_static()
            sf.save()
            return self._after2(0)
        sf.zap_deps1()
        (dodir, dofile, basedir, basename, ext) = paths.find_do_file(sf)
        if not dofile:
            if os.path.exists(t):
                sf.set_static()
                sf.save()
                return self._after2(0)
            else:
                err('no rule to redo %r\n' % t)
                return self._after2(1)
        unlink(self.tmpname1)
        unlink(self.tmpname2)
        ffd = os.open(self.tmpname1, os.O_CREAT|os.O_RDWR|os.O_EXCL, 0666)
        close_on_exec(ffd, True)
        self.f = os.fdopen(ffd, 'w+')
        # this will run in the dofile's directory, so use only basenames here
        arg1 = basename + ext  # target name (including extension)
        arg2 = basename        # target name (without extension)
        argv = ['sh', '-e',
                dofile,
                arg1,
                arg2,
                # temp output file name
                state.relpath(os.path.abspath(self.tmpname2), dodir),
                ]
        if vars.VERBOSE: argv[1] += 'v'
        if vars.XTRACE: argv[1] += 'x'
        firstline = open(os.path.join(dodir, dofile)).readline().strip()
        if firstline.startswith('#!/'):
            argv[0:2] = firstline[2:].split(' ')
        # make sure to create the logfile *before* writing the log about it.
        # that way redo-log won't trace into an obsolete logfile.
        if vars.LOG: open(state.logname(self.sf.id), 'w')
        meta('do', state.target_relpath(t))
        self.dodir = dodir
        self.basename = basename
        self.ext = ext
        self.argv = argv
        sf.is_generated = True
        sf.save()
        dof = state.File(name=os.path.join(dodir, dofile))
        dof.set_static()
        dof.save()
        state.commit()
        jwack.start_job(t, self._do_subproc, self._after)

    def _start_unlocked(self, dirty):
        # out-of-band redo of some sub-objects.  This happens when we're not
        # quite sure if t needs to be built or not (because some children
        # look dirty, but might turn out to be clean thanks to checksums). 
        # We have to call redo-unlocked to figure it all out.
        #
        # Note: redo-unlocked will handle all the updating of sf, so we
        # don't have to do it here, nor call _after1.  However, we have to
        # hold onto the lock because otherwise we would introduce a race
        # condition; that's why it's called redo-unlocked, because it doesn't
        # grab a lock.
        here = os.getcwd()
        def _fix(p):
            return state.relpath(os.path.join(vars.BASE, p), here)
        argv = (['redo-unlocked', _fix(self.sf.name)] +
                [_fix(d.name) for d in dirty])
        meta('check', state.target_relpath(self.t))
        state.commit()
        def run():
            os.environ['REDO_DEPTH'] = vars.DEPTH + '  '
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # python ignores SIGPIPE
            os.execvp(argv[0], argv)
            assert(0)
            # returns only if there's an exception
        def after(t, rv):
            return self._after2(rv)
        jwack.start_job(self.t, run, after)

    def _do_subproc(self):
        # careful: REDO_PWD was the PWD relative to the STARTPATH at the time
        # we *started* building the current target; but that target ran
        # redo-ifchange, and it might have done it from a different directory
        # than we started it in.  So os.getcwd() might be != REDO_PWD right
        # now.
        assert(state.is_flushed())
        dn = self.dodir
        newp = os.path.realpath(dn)
        os.environ['REDO_PWD'] = state.relpath(newp, vars.STARTDIR)
        os.environ['REDO_TARGET'] = self.basename + self.ext
        os.environ['REDO_DEPTH'] = vars.DEPTH + '  '
        vars.add_lock(str(self.lock.fid))
        if dn:
            os.chdir(dn)
        os.dup2(self.f.fileno(), 1)
        os.close(self.f.fileno())
        close_on_exec(1, False)
        if vars.LOG:
            cur_inode = str(os.fstat(2).st_ino)
            if not vars.LOG_INODE or cur_inode == vars.LOG_INODE:
                # .do script has *not* redirected stderr, which means we're
                # using redo-log's log saving mode.  That means subprocs
                # should be logged to their own file.  If the .do script
                # *does* redirect stderr, that redirection should be inherited
                # by subprocs, so we'd do nothing.
                logf = open(state.logname(self.sf.id), 'w')
                new_inode = str(os.fstat(logf.fileno()).st_ino)
                os.environ['REDO_LOG'] = '1'  # .do files can check this
                os.environ['REDO_LOG_INODE'] = new_inode
                os.dup2(logf.fileno(), 2)
                close_on_exec(2, False)
                logf.close()
        else:
            if 'REDO_LOG_INODE' in os.environ:
                del os.environ['REDO_LOG_INODE']
            os.environ['REDO_LOG'] = ''
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # python ignores SIGPIPE
        if vars.VERBOSE or vars.XTRACE:
            logs.write('* %s' % ' '.join(self.argv).replace('\n', ' '))
        os.execvp(self.argv[0], self.argv)
        # FIXME: it would be nice to log the exit code to logf.
        #  But that would have to happen in the parent process, which doesn't
        #  have logf open.
        assert(0)
        # returns only if there's an exception

    def _after(self, t, rv):
        try:
            state.check_sane()
            rv = self._after1(t, rv)
            state.commit()
        finally:
            self._after2(rv)

    def _after1(self, t, rv):
        f = self.f
        before_t = self.before_t
        after_t = _try_stat(t)
        st1 = os.fstat(f.fileno())
        st2 = _try_stat(self.tmpname2)
        if (after_t and 
            (not before_t or before_t.st_mtime != after_t.st_mtime) and
            not stat.S_ISDIR(after_t.st_mode)):
            err('%s modified %s directly!\n' % (self.argv[2], t))
            err('...you should update $3 (a temp file) or stdout, not $1.\n')
            rv = 206
        elif st2 and st1.st_size > 0:
            err('%s wrote to stdout *and* created $3.\n' % self.argv[2])
            err('...you should write status messages to stderr, not stdout.\n')
            rv = 207
        if rv==0:
            if st2:
                try:
                    os.rename(self.tmpname2, t)
                except OSError, e:
                    dnt = os.path.dirname(t)
                    if not os.path.exists(dnt):
                        err('%s: target dir %r does not exist!\n' % (t, dnt))
                    else:
                        err('%s: rename %s: %s\n' % (t, self.tmpname2, e))
                        raise
                os.unlink(self.tmpname1)
            elif st1.st_size > 0:
                try:
                    os.rename(self.tmpname1, t)
                except OSError, e:
                    if e.errno == errno.ENOENT:
                        unlink(t)
                    else:
                        err('%s: can\'t save stdout to %r: %s\n' %
                            (self.argv[2], t, e.strerror))
                        rv = 1000
                if st2:
                    os.unlink(self.tmpname2)
            else: # no output generated at all; that's ok
                unlink(self.tmpname1)
                unlink(t)
            sf = self.sf
            sf.refresh()
            sf.is_generated = True
            sf.is_override = False
            if sf.is_checked() or sf.is_changed():
                # it got checked during the run; someone ran redo-stamp.
                # update_stamp would call set_changed(); we don't want that
                sf.stamp = sf.read_stamp()
            else:
                sf.csum = None
                sf.update_stamp()
                sf.set_changed()
        else:
            unlink(self.tmpname1)
            unlink(self.tmpname2)
            sf = self.sf
            sf.set_failed()
        sf.zap_deps2()
        sf.save()
        f.close()
        meta('done', '%d %s' % (rv, state.target_relpath(self.t)))
        return rv

    def _after2(self, rv):
        try:
            self.donefunc(self.t, rv)
            assert(self.lock.owned)
        finally:
            self.lock.unlock()


def main(targets, shouldbuildfunc):
    retcode = [0]  # a list so that it can be reassigned from done()
    if vars.SHUFFLE:
        import random
        random.shuffle(targets)

    locked = []

    def done(t, rv):
        if rv:
            retcode[0] = 1
    
    if vars.TARGET and not vars.UNLOCKED:
        me = os.path.join(vars.STARTDIR, 
                          os.path.join(vars.PWD, vars.TARGET))
        myfile = state.File(name=me)
        selflock = state.Lock(state.LOG_LOCK_MAGIC + myfile.id)
    else:
        selflock = myfile = me = None
    
    def cheat():
        if not selflock: return 0
        selflock.trylock()
        if not selflock.owned:
            # redo-log already owns it: let's cheat.
            # Give ourselves one extra token so that the "foreground" log
            # can always make progress.
            return 1
        else:
            # redo-log isn't watching us (yet)
            selflock.unlock()
            return 0

    # In the first cycle, we just build as much as we can without worrying
    # about any lock contention.  If someone else has it locked, we move on.
    seen = {}
    lock = None
    for t in targets:
        if not t:
            err('cannot build the empty target ("").\n')
            retcode[0] = 204
            break
        assert(state.is_flushed())
        if t in seen:
            continue
        seen[t] = 1
        if not jwack.has_token():
            state.commit()
        jwack.ensure_token_or_cheat(t, cheat)
        if retcode[0] and not vars.KEEP_GOING:
            break
        if not state.check_sane():
            err('.redo directory disappeared; cannot continue.\n')
            retcode[0] = 205
            break
        f = state.File(name=t)
        lock = state.Lock(f.id)
        if vars.UNLOCKED:
            lock.owned = True
        else:
            lock.trylock()
        if not lock.owned:
            meta('locked', state.target_relpath(t))
            locked.append((f.id,t,f.name))
        else:
            # We had to create f before we had a lock, because we need f.id
            # to make the lock.  But someone may have updated the state
            # between then and now.
            # FIXME: separate obtaining the fid from creating the File.
            # FIXME: maybe integrate locking into the File object?
            f.refresh()
            BuildJob(t, f, lock, shouldbuildfunc, done).start()
        state.commit()
        assert(state.is_flushed())
        lock = None

    del lock

    # Now we've built all the "easy" ones.  Go back and just wait on the
    # remaining ones one by one.  There's no reason to do it any more
    # efficiently, because if these targets were previously locked, that
    # means someone else was building them; thus, we probably won't need to
    # do anything.  The only exception is if we're invoked as redo instead
    # of redo-ifchange; then we have to redo it even if someone else already
    # did.  But that should be rare.
    while locked or jwack.running():
        state.commit()
        jwack.wait_all()
        assert jwack._mytokens == 0
        jwack.ensure_token_or_cheat('self', cheat)
        # at this point, we don't have any children holding any tokens, so
        # it's okay to block below.
        if retcode[0] and not vars.KEEP_GOING:
            break
        if locked:
            if not state.check_sane():
                err('.redo directory disappeared; cannot continue.\n')
                retcode[0] = 205
                break
            fid,t,fname = locked.pop(0)
            lock = state.Lock(fid)
            backoff = 0.01
            lock.trylock()
            while not lock.owned:
                # Don't spin with 100% CPU while we fight for the lock.
                import random
                time.sleep(random.random() * min(backoff, 1.0))
                backoff *= 2
                # after printing this line, redo-log will recurse into t,
                # whether it's us building it, or someone else.
                meta('waiting', state.target_relpath(t))
                try:
                    lock.check()
                except state.CyclicDependencyError:
                    err('cyclic dependency while building %s\n' % _nice(t))
                    retcode[0] = 208
                    return retcode[0]
                # this sequence looks a little silly, but the idea is to
                # give up our personal token while we wait for the lock to
                # be released; but we should never run ensure_token() while
                # holding a lock, or we could cause deadlocks.
                jwack.release_mine()
                lock.waitlock()
                # now t is definitely free, so we get to decide whether
                # to build it.
                lock.unlock()
                jwack.ensure_token_or_cheat(t, cheat)
                lock.trylock()
            assert(lock.owned)
            meta('unlocked', state.target_relpath(t))
            if state.File(name=t).is_failed():
                err('%s: failed in another thread\n' % _nice(t))
                retcode[0] = 2
                lock.unlock()
            else:
                BuildJob(t, state.File(id=fid), lock,
                         shouldbuildfunc, done).start()
            lock = None
    state.commit()
    return retcode[0]
