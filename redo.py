#!/usr/bin/python
import sys, os, glob
import options, jwack, atoi

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are run
shuffle    randomize the build order to find dependency bugs
"""
o = options.Options('redo', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra or ['all']

if opt.debug:
    os.environ['REDO_DEBUG'] = str(opt.debug or 0)
if opt.verbose:
    os.environ['REDO_VERBOSE'] = '1'
if opt.shuffle:
    os.environ['REDO_SHUFFLE'] = '1'

is_root = False
if not os.environ.get('REDO_BASE', ''):
    is_root = True
    base = os.path.commonprefix([os.path.abspath(os.path.dirname(t))
                                 for t in targets] + [os.getcwd()])
    bsplit = base.split('/')
    for i in range(len(bsplit)-1, 0, -1):
        newbase = '/'.join(bsplit[:i])
        if os.path.exists(newbase + '/.redo'):
            base = newbase
            break
    os.environ['REDO_BASE'] = base
    os.environ['REDO_STARTDIR'] = os.getcwd()
    os.environ['REDO'] = os.path.abspath(sys.argv[0])


import vars, builder
from helpers import *


if is_root:
    # FIXME: just wiping out all the locks is kind of cheating.  But we
    # only do this from the toplevel redo process, so unless the user
    # deliberately starts more than one redo on the same repository, it's
    # sort of ok.
    mkdirp('%s/.redo' % base)
    for f in glob.glob('%s/.redo/lock*' % base):
        os.unlink(f)
    for f in glob.glob('%s/.redo/mark^*' % base):
        os.unlink(f)


if not vars.DEPTH:
    # toplevel call to redo
    exenames = [os.path.abspath(sys.argv[0]), os.path.realpath(sys.argv[0])]
    if exenames[0] == exenames[1]:
        exenames = [exenames[0]]
    dirnames = [os.path.dirname(p) for p in exenames]
    os.environ['PATH'] = ':'.join(dirnames) + ':' + os.environ['PATH']

try:
    j = atoi.atoi(opt.jobs or 1)
    if j < 1 or j > 1000:
        err('invalid --jobs value: %r\n' % opt.jobs)
    jwack.setup(j)
    try:
        retcode = builder.main(targets, builder.build)
    finally:
        jwack.force_return_tokens()
    if retcode:
        err('exiting: %d\n' % retcode)
    sys.exit(retcode)
except KeyboardInterrupt:
    sys.exit(200)
