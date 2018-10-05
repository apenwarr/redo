#!/usr/bin/env python
import sys, os

import vars_init
vars_init.init([])

import builder
from log import err

if len(sys.argv[1:]) != 1:
    err('%s: exactly one argument expected.\n' % sys.argv[0])
    sys.exit(1)

want = sys.argv[1]
for dodir,dofile,basedir,basename,ext in builder.possible_do_files(os.path.abspath(want)):
    dopath = os.path.join('/', dodir, dofile)
    relpath = os.path.relpath(dopath, '.')
    exists = os.path.exists(dopath)
    assert('\n' not in relpath)
    if exists:
      print '+', relpath
      assert('\n' not in basename)
      assert('\n' not in ext)
      print '1', basename+ext
      print '2', basename
      sys.exit(0)
    else:
      print '-', relpath
sys.exit(1)   # no appropriate dofile found
