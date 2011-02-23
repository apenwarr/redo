#!/usr/bin/env python
import sys, os

import vars_init
vars_init.init([])

import state
from log import err

if len(sys.argv[1:]) != 0:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)

for f in state.files():
    if f.name.startswith('//'):
        continue  # special name, ignore
    if not f.is_generated and f.read_stamp() != state.STAMP_MISSING:
        print f.nicename()
