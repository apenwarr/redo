"""redo-targets: list the known targets (not sources)."""
import sys, os
from . import env, logs, state


def main():
    if len(sys.argv[1:]) != 0:
        sys.stderr.write('%s: no arguments expected.\n' % sys.argv[0])
        sys.exit(1)

    state.init([])
    logs.setup(
        tty=sys.stderr, parent_logs=env.v.LOG,
        pretty=env.v.PRETTY, color=env.v.COLOR)

    cwd = os.getcwd()
    for f in state.files():
        if f.is_target():
            print state.relpath(os.path.join(env.v.BASE, f.name), cwd)


if __name__ == '__main__':
    main()
