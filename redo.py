#!/usr/bin/python
import sys, os, subprocess
import options

optspec = """
redo [targets...]
--
d,debug    print dependency checks as they happen
v,verbose  print commands as they are run
"""
o = options.Options('redo', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra or ['it']

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

import vars
from helpers import *


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


def build(t):
    unlink(sname('dep', t))
    open(sname('dep', t), 'w').close()
    dofile = find_do_file(t)
    if not dofile:
        if os.path.exists(t):  # an existing source file
            stamp(t)
            return  # success
        else:
            raise Exception('no rule to make %r' % t)
    stamp(dofile)
    unlink(t)
    tmpname = '%s.redo.tmp' % t
    unlink(tmpname)
    f = open(tmpname, 'w+')
    argv = ['sh', '-e', os.path.basename(dofile),
            os.path.basename(t), 'FIXME', os.path.basename(tmpname)]
    if vars.VERBOSE:
        argv[1] += 'v'
    log('%s\n' % t)
    rv = subprocess.call(argv, preexec_fn=lambda: _preexec(t),
                         stdout=f.fileno())
    st = os.stat(tmpname)
    #log('rv: %d (%d bytes) (%r)\n' % (rv, st.st_size, dofile))
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
        raise Exception('non-zero return code building %r' % t)


if not vars.DEPTH:
    # toplevel call to redo
    exenames = [os.path.abspath(sys.argv[0]), os.path.realpath(sys.argv[0])]
    if exenames[0] == exenames[1]:
        exenames = [exenames[0]]
    dirnames = [os.path.dirname(p) for p in exenames]
    os.environ['PATH'] = ':'.join(dirnames) + ':' + os.environ['PATH']

startdir = os.getcwd()
for t in targets:
    mkdirp('%s/.redo' % vars.BASE)
    os.chdir(startdir)
    
    if vars.TARGET:
        add_dep(vars.TARGET, 'm', t)
    build(t)
