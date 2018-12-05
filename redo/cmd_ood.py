import sys, os
import env, state, deps
from logs import err

cache = {}


def is_checked(f):
    return cache.get(f.id, 0)


def set_checked(f):
    cache[f.id] = 1


def log_override(name):
    pass


def main():
    if len(sys.argv[1:]) != 0:
        err('%s: no arguments expected.\n' % sys.argv[0])
        sys.exit(1)

    state.init([])
    cwd = os.getcwd()
    for f in state.files():
        if f.is_target():
            if deps.isdirty(f,
                            depth='',
                            max_changed=env.v.RUNID,
                            already_checked=[],
                            is_checked=is_checked,
                            set_checked=set_checked,
                            log_override=log_override):
                print state.relpath(os.path.join(env.v.BASE, f.name), cwd)


if __name__ == '__main__':
    main()
