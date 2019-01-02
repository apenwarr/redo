"""Code for parallel-building a set of targets, if needed."""
import errno, os, stat, signal, sys, tempfile, time
from . import cycles, env, jobserver, logs, state, paths
from .helpers import unlink, close_on_exec
from .logs import debug2, err, warn, meta


def _nice(t):
    return state.relpath(t, env.v.STARTDIR)


def _try_stat(filename):
    try:
        return os.lstat(filename)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return None
        else:
            raise


log_reader_pid = None


def close_stdin():
    f = open('/dev/null')
    os.dup2(f.fileno(), 0)
    f.close()


def start_stdin_log_reader(status, details, pretty, color,
                           debug_locks, debug_pids):
    """Redirect stderr to a redo-log instance with the given options.

    Then we automatically run logs.setup() to send the right data format
    to that redo-log instance.

    After this, be sure to run await_log_reader() before exiting.
    """
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
        logs.setup(tty=sys.stderr, parent_logs=True, pretty=False, color=False)
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
        except Exception, e:  # pylint: disable=broad-except
            sys.stderr.write('redo-log: exec: %s\n' % e)
        finally:
            os._exit(99)


def await_log_reader():
    """Await the redo-log instance we redirected stderr to, if any."""
    if not env.v.LOG:
        return
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


class _BuildJob(object):
    def __init__(self, t, sf, lock, shouldbuildfunc, donefunc):
        self.t = t  # original target name, not relative to env.v.BASE
        self.sf = sf
        self.tmpname = None
        self.lock = lock
        self.shouldbuildfunc = shouldbuildfunc
        self.donefunc = donefunc
        self.before_t = _try_stat(self.t)

        # attributes of the running process
        self.outfile = None

    def start(self):
        """Actually start running this job in a subproc, if needed."""
        assert self.lock.owned
        try:
            try:
                is_target, dirty = self.shouldbuildfunc(self.t)
            except cycles.CyclicDependencyError:
                err('cyclic dependency while checking %s\n' % _nice(self.t))
                raise ImmediateReturn(208)
            if not dirty:
                # target doesn't need to be built; skip the whole task
                if is_target:
                    meta('unchanged', state.target_relpath(self.t))
                return self._finalize(0)
        except ImmediateReturn, e:
            return self._finalize(e.rv)

        if env.v.NO_OOB or dirty == True:  # pylint: disable=singleton-comparison
            self._start_self()
        else:
            self._start_deps_unlocked(dirty)

    def _start_self(self):
        """Run jobserver.start() to build this object's target file."""
        assert self.lock.owned
        t = self.t
        sf = self.sf
        newstamp = sf.read_stamp()
        if (sf.is_generated and
                newstamp != state.STAMP_MISSING and
                (sf.is_override or state.detect_override(sf.stamp, newstamp))):
            state.warn_override(_nice(t))
            if not sf.is_override:
                warn('%s - old: %r\n' % (_nice(t), sf.stamp))
                warn('%s - new: %r\n' % (_nice(t), newstamp))
                sf.set_override()
            sf.save()
            # fall through and treat it the same as a static file
        if (os.path.exists(t) and not os.path.isdir(t + '/.')
                and (sf.is_override or not sf.is_generated)):
            # an existing source file that was not generated by us.
            # This step is mentioned by djb in his notes.
            # For example, a rule called default.c.do could be used to try
            # to produce hello.c, but we don't want that to happen if
            # hello.c was created by the end user.
            debug2("-- static (%r)\n" % t)
            sf.set_static()
            sf.save()
            return self._finalize(0)
        sf.zap_deps1()
        (dodir, dofile, _, basename, ext) = paths.find_do_file(sf)
        if not dofile:
            if os.path.exists(t):
                sf.set_static()
                sf.save()
                return self._finalize(0)
            else:
                err('no rule to redo %r\n' % t)
                return self._finalize(1)
        # There is no good place for us to pre-create a temp file for
        # stdout.  The target dir might not exist yet, or it might currently
        # exist but get wiped by the .do script.  Other dirs, like the one
        # containing the .do file, might be mounted readonly.  We can put it
        # in the system temp dir, but then we can't necessarily rename it to
        # the target filename because it might cross filesystem boundaries.
        # Also, if redo is interrupted, it would leave a temp file lying
        # around.  To avoid all this, use mkstemp() to create a temp file
        # wherever it wants to, and immediately unlink it, but keep a file
        # handle open.  When the .do script finishes, we can copy the
        # content out of that nameless file handle into a file in the same
        # dir as the target (which by definition must now exist, if you
        # wanted the target to exist).
        #
        # On the other hand, the $3 temp filename can be hardcoded to be in
        # the target directory, even if that directory does not exist.
        # It's not *redo*'s job to create that file.  The .do file will
        # create it, if it wants, and it's the .do file's job to first ensure
        # that the directory exists.
        tmpbase = os.path.join(dodir, basename + ext)
        self.tmpname = tmpbase + '.redo.tmp'
        unlink(self.tmpname)
        ffd, fname = tempfile.mkstemp(prefix='redo.', suffix='.tmp')
        close_on_exec(ffd, True)
        os.unlink(fname)
        self.outfile = os.fdopen(ffd, 'w+')
        # this will run in the dofile's directory, so use only basenames here
        arg1 = basename + ext  # target name (including extension)
        arg2 = basename        # target name (without extension)
        argv = ['sh', '-e',
                dofile,
                arg1,
                arg2,
                # $3 temp output file name
                state.relpath(os.path.abspath(self.tmpname), dodir),
               ]
        if env.v.VERBOSE:
            argv[1] += 'v'
        if env.v.XTRACE:
            argv[1] += 'x'
        firstline = open(os.path.join(dodir, dofile)).readline().strip()
        if firstline.startswith('#!/'):
            argv[0:2] = firstline[2:].split(' ')
        # make sure to create the logfile *before* writing the meta() about it.
        # that way redo-log won't trace into an obsolete logfile.
        if env.v.LOG:
            open(state.logname(self.sf.id), 'w')
        dof = state.File(name=os.path.join(dodir, dofile))
        dof.set_static()
        dof.save()
        state.commit()
        meta('do', state.target_relpath(t))
        def call_subproc():
            self._subproc(dodir, basename, ext, argv)
        def call_exited(t, rv):
            self._subproc_exited(t, rv, argv)
        jobserver.start(t, call_subproc, call_exited)

    def _start_deps_unlocked(self, dirty):
        """Run jobserver.start to build objects needed to check deps.

        Out-of-band redo of some sub-objects.  This happens when we're not
        quite sure if t needs to be built or not (because some children
        look dirty, but might turn out to be clean thanks to redo-stamp
        checksums).  We have to call redo-unlocked to figure it all out.

        Note: redo-unlocked will handle all the updating of sf, so we don't
        have to do it here, nor call _record_new_state.  However, we have to
        hold onto the lock because otherwise we would introduce a race
        condition; that's why it's called redo-unlocked, because it doesn't
        grab a lock.
        """
        # FIXME: redo-unlocked is kind of a weird hack.
        #  Maybe we should just start jobs to build the necessary deps
        #  directly from this process, and when done, reconsider building
        #  the target we started with.  But that makes this one process's
        #  build recursive, where currently it's flat.
        here = os.getcwd()
        def _fix(p):
            return state.relpath(os.path.join(env.v.BASE, p), here)
        argv = (['redo-unlocked', _fix(self.sf.name)] +
                list(set(_fix(d.name) for d in dirty)))
        meta('check', state.target_relpath(self.t))
        state.commit()
        def subtask():
            os.environ['REDO_DEPTH'] = env.v.DEPTH + '  '
            # python ignores SIGPIPE
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            os.execvp(argv[0], argv)
            assert 0
            # returns only if there's an exception
        def job_exited(t, rv):
            return self._finalize(rv)
        jobserver.start(self.t, jobfunc=subtask, donefunc=job_exited)

    def _subproc(self, dodir, basename, ext, argv):
        """The function by jobserver.start to exec the build script.

        This is run in the *child* process.
        """
        # careful: REDO_PWD was the PWD relative to the STARTPATH at the time
        # we *started* building the current target; but that target ran
        # redo-ifchange, and it might have done it from a different directory
        # than we started it in.  So os.getcwd() might be != REDO_PWD right
        # now.
        assert state.is_flushed()
        newp = os.path.realpath(dodir)
        os.environ['REDO_PWD'] = state.relpath(newp, env.v.STARTDIR)
        os.environ['REDO_TARGET'] = basename + ext
        os.environ['REDO_DEPTH'] = env.v.DEPTH + '  '
        cycles.add(self.lock.fid)
        if dodir:
            os.chdir(dodir)
        os.dup2(self.outfile.fileno(), 1)
        os.close(self.outfile.fileno())
        close_on_exec(1, False)
        if env.v.LOG:
            cur_inode = str(os.fstat(2).st_ino)
            if not env.v.LOG_INODE or cur_inode == env.v.LOG_INODE:
                # .do script has *not* redirected stderr, which means we're
                # using redo-log's log saving mode.  That means subprocs
                # should be logged to their own file.  If the .do script
                # *does* redirect stderr, that redirection should be inherited
                # by subprocs, so we'd do nothing.
                logf = open(state.logname(self.sf.id), 'w')
                new_inode = os.fstat(logf.fileno()).st_ino
                os.environ['REDO_LOG'] = '1'  # .do files can check this
                os.environ['REDO_LOG_INODE'] = str(new_inode)
                os.dup2(logf.fileno(), 2)
                close_on_exec(2, False)
                logf.close()
        else:
            if 'REDO_LOG_INODE' in os.environ:
                del os.environ['REDO_LOG_INODE']
            os.environ['REDO_LOG'] = ''
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # python ignores SIGPIPE
        if env.v.VERBOSE or env.v.XTRACE:
            logs.write('* %s' % ' '.join(argv).replace('\n', ' '))
        os.execvp(argv[0], argv)
        # FIXME: it would be nice to log the exit code to logf.
        #  But that would have to happen in the parent process, which doesn't
        #  have logf open.
        assert 0
        # returns only if there's an exception

    def _subproc_exited(self, t, rv, argv):
        """Called by the jobserver when our subtask exits.

        This is run in the *parent* process.
        """
        try:
            state.check_sane()
            rv = self._record_new_state(t, rv, argv)
            state.commit()
        finally:
            self._finalize(rv)

    def _record_new_state(self, t, rv, argv):
        """After a subtask finishes, handle its changes to the output file.

        This is run in the *parent* process.

        This includes renaming temp files into place and detecting mistakes
        (like writing directly to $1 instead of $3).  We also have to record
        the new file stamp data for the completed target.
        """
        outfile = self.outfile
        before_t = self.before_t
        after_t = _try_stat(t)
        st1 = os.fstat(outfile.fileno())
        st2 = _try_stat(self.tmpname)
        if (after_t and
                (not before_t or before_t.st_mtime != after_t.st_mtime) and
                not stat.S_ISDIR(after_t.st_mode)):
            err('%s modified %s directly!\n' % (argv[2], t))
            err('...you should update $3 (a temp file) or stdout, not $1.\n')
            rv = 206
        elif st2 and st1.st_size > 0:
            err('%s wrote to stdout *and* created $3.\n' % argv[2])
            err('...you should write status messages to stderr, not stdout.\n')
            rv = 207
        if rv == 0:
            # FIXME: race condition here between updating stamp/is_generated
            # and actually renaming the files into place.  There needs to
            # be some kind of two-stage commit, I guess.
            if st1.st_size > 0 and not st2:
                # script wrote to stdout.  Copy its contents to the tmpfile.
                unlink(self.tmpname)
                try:
                    newf = open(self.tmpname, 'w')
                except IOError, e:
                    dnt = os.path.dirname(os.path.abspath(t))
                    if not os.path.exists(dnt):
                        # This could happen, so report a simple error message
                        # that gives a hint for how to fix your .do script.
                        err('%s: target dir %r does not exist!\n' % (t, dnt))
                    else:
                        # This could happen for, eg. a permissions error on
                        # the target directory.
                        err('%s: copy stdout: %s\n' % (t, e))
                    rv = 209
                else:
                    self.outfile.seek(0)
                    while 1:
                        b = self.outfile.read(1024*1024)
                        if not b:
                            break
                        newf.write(b)
                    newf.close()
                    st2 = _try_stat(self.tmpname)
            if st2:
                # either $3 file was created *or* stdout was written to.
                # therefore tmpfile now exists.
                try:
                    # Atomically replace the target file
                    os.rename(self.tmpname, t)
                except OSError, e:
                    # This could happen for, eg. a permissions error on
                    # the target directory.
                    err('%s: rename %s: %s\n' % (t, self.tmpname, e))
                    rv = 209
            else: # no output generated at all; that's ok
                unlink(t)
            sf = self.sf
            sf.refresh()
            sf.is_generated = True
            sf.is_override = False
            if sf.is_checked() or sf.is_changed():
                # it got checked during the run; someone ran redo-stamp.
                # update_stamp would call set_changed(); we don't want that,
                # so only use read_stamp.
                sf.stamp = sf.read_stamp()
            else:
                sf.csum = None
                sf.update_stamp()
                sf.set_changed()
        else:
            unlink(self.tmpname)
            sf = self.sf
            sf.set_failed()
        sf.zap_deps2()
        sf.save()
        outfile.close()
        meta('done', '%d %s' % (rv, state.target_relpath(self.t)))
        return rv

    def _finalize(self, rv):
        """After a target is built, report completion and unlock.

        This is run in the *parent* process.
        Note: you usually need to call _record_new_state() first.
        """
        try:
            self.donefunc(self.t, rv)
            assert self.lock.owned
        finally:
            self.lock.unlock()


def run(targets, shouldbuildfunc):
    """Build the given list of targets, if necessary.

    Builds in parallel using whatever jobserver tokens can be obtained.

    Args:
      targets: a list of target filenames to consider building.
      shouldbuildfunc: a function(target) which determines whether the given
        target needs to be built, as of the time it is called.

    Returns:
      0 if all necessary targets returned exit code zero; nonzero otherwise.
    """
    retcode = [0]  # a list so that it can be reassigned from done()
    if env.v.SHUFFLE:
        import random
        random.shuffle(targets)

    locked = []

    def job_exited(t, rv):
        if rv:
            retcode[0] = 1

    if env.v.TARGET and not env.v.UNLOCKED:
        me = os.path.join(env.v.STARTDIR,
                          os.path.join(env.v.PWD, env.v.TARGET))
        myfile = state.File(name=me)
        selflock = state.Lock(state.LOG_LOCK_MAGIC + myfile.id)
    else:
        selflock = myfile = me = None

    def cheat():
        if not selflock:
            return 0
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
        assert state.is_flushed()
        if t in seen:
            continue
        seen[t] = 1
        if not jobserver.has_token():
            state.commit()
        jobserver.ensure_token_or_cheat(t, cheat)
        if retcode[0] and not env.v.KEEP_GOING:
            break
        if not state.check_sane():
            err('.redo directory disappeared; cannot continue.\n')
            retcode[0] = 205
            break
        f = state.File(name=t)
        lock = state.Lock(f.id)
        if env.v.UNLOCKED:
            lock.owned = True
        else:
            lock.trylock()
        if not lock.owned:
            meta('locked', state.target_relpath(t))
            locked.append((f.id, t, f.name))
        else:
            # We had to create f before we had a lock, because we need f.id
            # to make the lock.  But someone may have updated the state
            # between then and now.
            # FIXME: separate obtaining the fid from creating the File.
            # FIXME: maybe integrate locking into the File object?
            f.refresh()
            _BuildJob(t, f, lock,
                      shouldbuildfunc=shouldbuildfunc,
                      donefunc=job_exited).start()
        state.commit()
        assert state.is_flushed()
        lock = None

    del lock

    # Now we've built all the "easy" ones.  Go back and just wait on the
    # remaining ones one by one.  There's no reason to do it any more
    # efficiently, because if these targets were previously locked, that
    # means someone else was building them; thus, we probably won't need to
    # do anything.  The only exception is if we're invoked as redo instead
    # of redo-ifchange; then we have to redo it even if someone else already
    # did.  But that should be rare.
    while locked or jobserver.running():
        state.commit()
        jobserver.wait_all()
        assert jobserver._mytokens <= 1  # pylint: disable=protected-access
        jobserver.ensure_token_or_cheat('self', cheat)
        # at this point, we don't have any children holding any tokens, so
        # it's okay to block below.
        if retcode[0] and not env.v.KEEP_GOING:
            break
        if locked:
            if not state.check_sane():
                err('.redo directory disappeared; cannot continue.\n')
                retcode[0] = 205
                break
            fid, t, _ = locked.pop(0)
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
                except cycles.CyclicDependencyError:
                    err('cyclic dependency while building %s\n' % _nice(t))
                    retcode[0] = 208
                    return retcode[0]
                # this sequence looks a little silly, but the idea is to
                # give up our personal token while we wait for the lock to
                # be released; but we should never run ensure_token() while
                # holding a lock, or we could cause deadlocks.
                jobserver.release_mine()
                lock.waitlock()
                # now t is definitely free, so we get to decide whether
                # to build it.
                lock.unlock()
                jobserver.ensure_token_or_cheat(t, cheat)
                lock.trylock()
            assert lock.owned
            meta('unlocked', state.target_relpath(t))
            if state.File(name=t).is_failed():
                err('%s: failed in another thread\n' % _nice(t))
                retcode[0] = 2
                lock.unlock()
            else:
                _BuildJob(t, state.File(fid=fid), lock,
                          shouldbuildfunc=shouldbuildfunc,
                          donefunc=job_exited).start()
            lock = None
    state.commit()
    return retcode[0]
