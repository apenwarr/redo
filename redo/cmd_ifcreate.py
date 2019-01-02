"""redo-ifcreate: build the current target if these targets are created."""
import sys, os
from . import env, logs, state
from .logs import err


def main():
    try:
        env.inherit()
        logs.setup(
            tty=sys.stderr, parent_logs=env.v.LOG,
            pretty=env.v.PRETTY, color=env.v.COLOR)

        me = os.path.join(env.v.STARTDIR,
                          os.path.join(env.v.PWD, env.v.TARGET))
        f = state.File(name=me)
        for t in sys.argv[1:]:
            if not t:
                err('cannot build the empty target ("").\n')
                sys.exit(204)
            if os.path.exists(t):
                err('redo-ifcreate: error: %r already exists\n' % t)
                sys.exit(1)
            else:
                f.add_dep('c', t)
        state.commit()
    except KeyboardInterrupt:
        sys.exit(200)


if __name__ == '__main__':
    main()
