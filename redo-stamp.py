#!/usr/bin/env python
import sys, os
import vars, state
from log import err, debug2

if len(sys.argv) > 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)

if os.isatty(0):
    err('%s: you must provide the data to stamp on stdin\n' % sys.argv[0])
    sys.exit(1)

# hashlib is only available in python 2.5 or higher, but the 'sha' module
# produces a DeprecationWarning in python 2.6 or higher.  We want to support
# python 2.4 and above without any stupid warnings, so let's try using hashlib
# first, and downgrade if it fails.
try:
    import hashlib
except ImportError:
    import sha
    sh = sha.sha()
else:
    sh = hashlib.sha1()

while 1:
    b = os.read(0, 4096)
    sh.update(b)
    if not b: break

csum = sh.hexdigest()

if not vars.TARGET:
    sys.exit(0)

state.fix_chdir([])
f = state.File(vars.TARGET)
f._add('%s .' % csum)
