#!/usr/bin/python
import sys, os, subprocess, glob, time
import options

optspec = """
redo [targets...]
--
d,debug    print dependency checks as they happen
v,verbose  print commands as they are run
"""
o = options.Options('redo', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra or ['all']

if opt.debug:
    os.environ['REDO_DEBUG'] = '1'
if opt.verbose:
    os.environ['REDO_VERBOSE'] = '1'

if not os.environ.get('REDO_BASE', ''):
    base = os.path.commonprefix([os.path.abspath(os.path.dirname(t))
                                 for t in targets] + [os.getcwd()])
    bsplit = base.split('/')
    for i in range(len(bsplit)-1, 0, -1):
        newbase = '%s/.redo' % '/'.join(bsplit[:i])
        if os.path.exists(newbase):
            base = newbase
            break
    os.environ['REDO_BASE'] = base
    os.environ['REDO_STARTDIR'] = os.getcwd()

    # FIXME: just wiping out all the locks is kind of cheating.  But we
    # only do this from the toplevel redo process, so unless the user
    # deliberately starts more than one redo on the same repository, it's
    # sort of ok.
    for f in glob.glob('%s/lock.*' % base):
        unlink(f)

import vars
from helpers import *


class BuildError(Exception):
    pass
class BuildLocked(Exception):
    pass


def find_do_file(t):
    dofile = '%s.do' % t
    if os.path.exists(dofile):
        add_dep(t, 'm', dofile)
        return dofile
    else:
        add_dep(t, 'c', dofile)
        return None


def stamp(t):
    stampfile = sname('stamp', t)
    depfile = sname('dep', t)
    if not os.path.exists(vars.BASE + '/.redo'):
        # .redo might not exist in a 'make clean' target
        return
    open(stampfile, 'w').close()
    open(depfile, 'a').close()
    try:
        mtime = os.stat(t).st_mtime
    except OSError:
        mtime = 0
    os.utime(stampfile, (mtime, mtime))


def _preexec(t):
    os.environ['REDO_TARGET'] = t
    os.environ['REDO_DEPTH'] = vars.DEPTH + '  '
    dn = os.path.dirname(t)
    if dn:
        os.chdir(dn)


def _build(t):
    unlink(sname('dep', t))
    open(sname('dep', t), 'w').close()
    dofile = find_do_file(t)
    if not dofile:
        if os.path.exists(t):  # an existing source file
            stamp(t)
            return  # success
        else:
            raise BuildError('no rule to make %r' % t)
    stamp(dofile)
    unlink(t)
    tmpname = '%s.redo.tmp' % t
    unlink(tmpname)
    f = open(tmpname, 'w+')
    argv = [os.environ.get('SHELL', 'sh'), '-e',
            os.path.basename(dofile),
            os.path.basename(t), 'FIXME', os.path.basename(tmpname)]
    if vars.VERBOSE:
        argv[1] += 'v'
    log('%s\n' % relpath(t, vars.STARTDIR))
    rv = subprocess.call(argv, preexec_fn=lambda: _preexec(t),
                         stdout=f.fileno())
    st = os.stat(tmpname)
    stampfile = sname('stamp', t)
    if rv==0:
        if st.st_size:
            os.rename(tmpname, t)
        else:
            unlink(tmpname)
        stamp(t)
    else:
        unlink(tmpname)
        unlink(stampfile)
    f.close()
    if rv != 0:
        raise BuildError('%s: exit code %d' % (t,rv))


def build(t):
    lockname = sname('lock', t)
    try:
        fd = os.open(lockname, os.O_CREAT|os.O_EXCL)
    except OSError, e:
        if e.errno == errno.EEXIST:
            log('%s (locked...)\n' % relpath(t, vars.STARTDIR))
            raise BuildLocked(t)
        else:
            raise
    os.close(fd)
    try:
        return _build(t)
    finally:
        unlink(lockname)


if not vars.DEPTH:
    # toplevel call to redo
    exenames = [os.path.abspath(sys.argv[0]), os.path.realpath(sys.argv[0])]
    if exenames[0] == exenames[1]:
        exenames = [exenames[0]]
    dirnames = [os.path.dirname(p) for p in exenames]
    os.environ['PATH'] = ':'.join(dirnames) + ':' + os.environ['PATH']

try:
    retcode = 0
    locked = {}
    for t in targets:
        if os.path.exists('%s/all.do' % t):
            # t is a directory, but it has a default target
            t = '%s/all' % t
        mkdirp('%s/.redo' % vars.BASE)
        try:
            build(t)
        except BuildError, e:
            err('%s\n' % e)
            retcode = 1
        except BuildLocked, e:
            locked[t] = 1
    while locked:
        for l in locked.keys():
            lockname = sname('lock', t)
            stampname = sname('stamp', t)
            if not os.path.exists(lockname):
                relp = relpath(t, vars.STARTDIR)
                log('%s (...unlocked!)\n' % relp)
                if not os.path.exists(stampname):
                    err('%s: failed in another thread\n' % relp)
                    retcode = 2
                del locked[l]
        time.sleep(0.2)
    sys.exit(retcode)
except KeyboardInterrupt:
    sys.exit(200)
