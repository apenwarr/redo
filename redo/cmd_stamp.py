"""redo-stamp: tell redo to use a checksum when considering this target."""
import sys, os
from . import env, logs, state
from .logs import debug2


def main():
    if len(sys.argv) > 1:
        sys.stderr.write('%s: no arguments expected.\n' % sys.argv[0])
        sys.exit(1)

    if os.isatty(0):
        sys.stderr.write('%s: you must provide the data to stamp on stdin\n'
                         % sys.argv[0])
        sys.exit(1)

    env.inherit()
    logs.setup(
        tty=sys.stderr, parent_logs=env.v.LOG,
        pretty=env.v.PRETTY, color=env.v.COLOR)

    # hashlib is only available in python 2.5 or higher, but the 'sha'
    # module produces a DeprecationWarning in python 2.6 or higher.  We want
    # to support python 2.4 and above without any stupid warnings, so let's
    # try using hashlib first, and downgrade if it fails.
    try:
        import hashlib
    except ImportError:
        import sha
        sh = sha.sha()
    else:
        sh = hashlib.sha1()

    while 1:
        b = os.read(0, 4096)
        sh.update(b)
        if not b:
            break

    csum = sh.hexdigest()

    if not env.v.TARGET:
        sys.exit(0)

    me = os.path.join(env.v.STARTDIR,
                      os.path.join(env.v.PWD, env.v.TARGET))
    f = state.File(name=me)
    changed = (csum != f.csum)
    debug2('%s: old = %s\n' % (f.name, f.csum))
    debug2('%s: sum = %s (%s)\n' % (f.name, csum,
                                    changed and 'changed' or 'unchanged'))
    f.is_generated = True
    f.is_override = False
    f.failed_runid = None
    if changed:
        f.set_changed()  # update_stamp might skip this if mtime is identical
        f.csum = csum
    else:
        # unchanged
        f.set_checked()
    f.save()
    state.commit()


if __name__ == '__main__':
    main()
