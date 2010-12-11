#!/usr/bin/python
import sys, os
import state
from helpers import err

if len(sys.argv[1:]) < 2:
    err('%s: at least 2 arguments expected.\n' % sys.argv[0])
    sys.exit(1)

target = sys.argv[1]
deps = sys.argv[2:]

me = state.File(name=target)

os.environ['REDO_NO_OOB'] = '1'
argv = ['redo-ifchange'] + deps
rv = os.spawnvp(os.P_WAIT, argv[0], argv)
if rv:
    sys.exit(rv)

# we know our caller already owns the lock on target, so we don't have to
# acquire another one.
os.environ['REDO_UNLOCKED'] = '1'
argv = ['redo-ifchange', target]
rv = os.spawnvp(os.P_WAIT, argv[0], argv)
if rv:
    sys.exit(rv)
