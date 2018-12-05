import os, sys, traceback

import env_init
env_init.init(sys.argv[1:])

import env, state, builder, jobserver, deps
from logs import debug2, err

def should_build(t):
    f = state.File(name=t)
    if f.is_failed():
        raise builder.ImmediateReturn(32)
    dirty = deps.isdirty(f, depth='', max_changed=env.RUNID,
                         already_checked=[])
    return f.is_generated, dirty == [f] and deps.DIRTY or dirty


def main():
    rv = 202
    try:
        if env_init.is_toplevel and env.LOG:
            builder.close_stdin()
            builder.start_stdin_log_reader(
                status=True, details=True,
                pretty=True, color=True, debug_locks=False, debug_pids=False)
        if env.TARGET and not env.UNLOCKED:
            me = os.path.join(env.STARTDIR,
                              os.path.join(env.PWD, env.TARGET))
            f = state.File(name=me)
            debug2('TARGET: %r %r %r\n'
                   % (env.STARTDIR, env.PWD, env.TARGET))
        else:
            f = me = None
            debug2('redo-ifchange: not adding depends.\n')
        jobserver.setup(1)
        try:
            targets = sys.argv[1:]
            if f:
                for t in targets:
                    f.add_dep('m', t)
                f.save()
                state.commit()
            rv = builder.main(targets, should_build)
        finally:
            try:
                state.rollback()
            finally:
                try:
                    jobserver.force_return_tokens()
                except Exception, e:  # pylint: disable=broad-except
                    traceback.print_exc(100, sys.stderr)
                    err('unexpected error: %r\n' % e)
                    rv = 1
    except KeyboardInterrupt:
        if env_init.is_toplevel:
            builder.await_log_reader()
        sys.exit(200)
    state.commit()
    if env_init.is_toplevel:
        builder.await_log_reader()
    sys.exit(rv)


if __name__ == '__main__':
    main()
