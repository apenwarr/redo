#!/usr/bin/env python
"""Calculate the sha256 digest of a given file."""
import hashlib, os, subprocess, sys

subprocess.check_call([
    'redo-ifchange',
    sys.argv[2],
], close_fds=False)

h = hashlib.sha256()
f = open(sys.argv[2], 'rb')
while 1:
    b = f.read(65536)
    if not b: break
    h.update(b)
open(sys.argv[3], 'w').write(h.hexdigest() + '\n')
