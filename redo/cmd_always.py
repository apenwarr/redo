"""redo-always: tell redo that the current target is always out of date."""
import sys, os
from . import env, logs, state


def main():
    try:
        env.inherit()
        logs.setup(
            tty=sys.stderr, parent_logs=env.v.LOG,
            pretty=env.v.PRETTY, color=env.v.COLOR)

        me = os.path.join(env.v.STARTDIR,
                          os.path.join(env.v.PWD, env.v.TARGET))
        f = state.File(name=me)
        f.add_dep('m', state.ALWAYS)
        always = state.File(name=state.ALWAYS)
        always.stamp = state.STAMP_MISSING
        always.set_changed()
        always.save()
        state.commit()
    except KeyboardInterrupt:
        sys.exit(200)


if __name__ == '__main__':
    main()
