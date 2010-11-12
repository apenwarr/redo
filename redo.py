#!/usr/bin/python
import sys, os, subprocess
import options
from helpers import *

optspec = """
redo [targets...]
--
ifchange   something something
"""
o = options.Options('redo', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra or ['it']


def find_do_file(t):
    p = '%s.do' % t
    if os.path.exists(p):
        return p
    else:
        return None
    

def build(t):
    dofile = find_do_file(t)
    if not dofile:
        if os.path.exists(t):  # an existing source file
            return  # success
        else:
            raise Exception('no rule to make %r' % t)
    unlink(t)
    os.putenv('REDO_TARGET', t)
    depth = os.getenv('REDO_DEPTH', '')
    os.putenv('REDO_DEPTH', depth + '  ')
    tmpname = '%s.redo.tmp' % t
    unlink(tmpname)
    f = open(tmpname, 'w+')
    argv = ['sh', '-e', dofile, t, 'FIXME', tmpname]
    log('redo: %s%s\n' % (depth, t))
    rv = subprocess.call(argv, stdout=f.fileno())
    st = os.stat(tmpname)
    #log('rv: %d (%d bytes) (%r)\n' % (rv, st.st_size, dofile))
    if rv==0 and st.st_size:
        os.rename(tmpname, t)
        #log('made %r\n' % t)
    else:
        unlink(tmpname)
    f.close()
    if rv != 0:
        raise Exception('non-zero return code building %r' % t)

for t in targets:
    build(t)
