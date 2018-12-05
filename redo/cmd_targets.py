import sys, os

import env_init
env_init.init([])

import state, env
from logs import err


def main():
    if len(sys.argv[1:]) != 0:
        err('%s: no arguments expected.\n' % sys.argv[0])
        sys.exit(1)

    cwd = os.getcwd()
    for f in state.files():
        if f.is_target():
            print state.relpath(os.path.join(env.BASE, f.name), cwd)


if __name__ == '__main__':
    main()
