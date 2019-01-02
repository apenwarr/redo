"""redo-whichdo: list the set of .do files considered to build a target."""
import sys, os
from . import env, logs, paths
from .logs import err


def main():
    if len(sys.argv[1:]) != 1:
        sys.stderr.write('%s: exactly one argument expected.\n' % sys.argv[0])
        sys.exit(1)

    env.init_no_state()
    logs.setup(
        tty=sys.stderr, parent_logs=env.v.LOG,
        pretty=env.v.PRETTY, color=env.v.COLOR)

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
