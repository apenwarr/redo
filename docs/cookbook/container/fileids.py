#!/usr/bin/env python
import hashlib, os, stat, sys

for name in sys.stdin:
    name = name[:-1]  # skip terminating newline
    st = os.lstat(name)
    if stat.S_ISREG(st.st_mode):
        h = hashlib.sha256()
        f = open(name, 'rb')
        while 1:
            b = f.read(65536)
            if not b: break
            h.update(b)
        digest = h.hexdigest()
    elif stat.S_ISLNK(st.st_mode):
        digest = hashlib.sha256(os.readlink(name).encode('utf8')).hexdigest()
    else:
        digest = '0'
    print('%s %07o-%s-%s-%s' % (
        name,
        st.st_mode, st.st_uid, st.st_gid, digest))
