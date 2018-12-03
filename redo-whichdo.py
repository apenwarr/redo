#!/usr/bin/env python2
import sys, os

import vars_init
vars_init.init_no_state()

import paths
from logs import err


def main():
    if len(sys.argv[1:]) != 1:
        err('%s: exactly one argument expected.\n' % sys.argv[0])
        sys.exit(1)

    want = sys.argv[1]
    if not want:
        err('cannot build the empty target ("").\n')
        sys.exit(204)

    abswant = os.path.abspath(want)
    pdf = paths.possible_do_files(abswant)
    for dodir, dofile, basedir, basename, ext in pdf:
        dopath = os.path.join('/', dodir, dofile)
        relpath = os.path.relpath(dopath, '.')
        exists = os.path.exists(dopath)
        assert '\n' not in relpath
        print relpath
        if exists:
            sys.exit(0)
    sys.exit(1)   # no appropriate dofile found


if __name__ == '__main__':
    main()
