#!/usr/bin/env python
import sys, os
import options
from helpers import atoi

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are read from .do files (variables intact)
x,xtrace   print commands as they are executed (variables expanded)
k,keep-going  keep going as long as possible even if some targets fail
shuffle    randomize the build order to find dependency bugs
debug-locks  print messages about file locking (useful for debugging)
debug-pids   print process ids as part of log messages (useful for debugging)
version    print the current version and exit
old-args   use old-style definitions of $1,$2,$3 (deprecated)
"""
o = options.Options(optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra

if opt.version:
    import version
    print version.TAG
    sys.exit(0)
if opt.debug:
    os.environ['REDO_DEBUG'] = str(opt.debug or 0)
if opt.verbose:
    os.environ['REDO_VERBOSE'] = '1'
if opt.xtrace:
    os.environ['REDO_XTRACE'] = '1'
if opt.keep_going:
    os.environ['REDO_KEEP_GOING'] = '1'
if opt.shuffle:
    os.environ['REDO_SHUFFLE'] = '1'
if opt.debug_locks:
    os.environ['REDO_DEBUG_LOCKS'] = '1'
if opt.debug_pids:
    os.environ['REDO_DEBUG_PIDS'] = '1'
if opt.old_args:
    os.environ['REDO_OLD_ARGS'] = '1'

import vars_init
vars_init.init(targets)

import vars, state, builder, jwack
from log import warn, err

try:
    for t in targets:
        if os.path.exists(t):
            f = state.File(name=t)
            if not f.is_generated:
                warn('%s: exists and not marked as generated; not redoing.\n'
                     % f.nicename())
    
    j = atoi(opt.jobs or 1)
    if j < 1 or j > 1000:
        err('invalid --jobs value: %r\n' % opt.jobs)
    jwack.setup(j)
    try:
        retcode = builder.main(targets, lambda t: True)
    finally:
        jwack.force_return_tokens()
    sys.exit(retcode)
except KeyboardInterrupt:
    sys.exit(200)
