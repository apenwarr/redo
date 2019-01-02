"""redo: build the listed targets whether they need it or not."""
#
# Copyright 2010-2018 Avery Pennarun and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys, os, traceback
from . import builder, env, jobserver, logs, options, state
from .atoi import atoi
from .logs import warn, err

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are read from .do files (variables intact)
x,xtrace   print commands as they are executed (variables expanded)
k,keep-going  keep going as long as possible even if some targets fail
shuffle    randomize the build order to find dependency bugs
version    print the current version and exit

 redo-log options:
no-log     don't capture error output, just let it flow straight to stderr
no-details only show 'redo' recursion trace (to see more later, use redo-log)
no-status  don't display build summary line at the bottom of the screen
no-pretty  don't pretty-print logs, show raw @@REDO output instead
no-color   disable ANSI color; --color to force enable (default: auto)
debug-locks  print messages about file locking (useful for debugging)
debug-pids   print process ids as part of log messages (useful for debugging)
"""

def main():
    o = options.Options(optspec)
    (opt, flags, extra) = o.parse(sys.argv[1:])

    targets = extra

    if opt.version:
        from . import version
        print version.TAG
        sys.exit(0)
    if opt.debug:
        os.environ['REDO_DEBUG'] = str(opt.debug or 0)
    if opt.verbose:
        os.environ['REDO_VERBOSE'] = '1'
    if opt.xtrace:
        os.environ['REDO_XTRACE'] = '1'
    if opt.keep_going:
        os.environ['REDO_KEEP_GOING'] = '1'
    if opt.shuffle:
        os.environ['REDO_SHUFFLE'] = '1'
    if opt.debug_locks:
        os.environ['REDO_DEBUG_LOCKS'] = '1'
    if opt.debug_pids:
        os.environ['REDO_DEBUG_PIDS'] = '1'
    # These might get overridden in subprocesses in builder.py
    def _set_defint(name, val):
        os.environ[name] = os.environ.get(name, str(int(val)))
    _set_defint('REDO_LOG', opt.log)
    _set_defint('REDO_PRETTY', opt.pretty)
    _set_defint('REDO_COLOR', opt.color)

    try:
        state.init(targets)
        if env.is_toplevel and not targets:
            targets = ['all']
        j = atoi(opt.jobs)
        if env.is_toplevel and (env.v.LOG or j > 1):
            builder.close_stdin()
        if env.is_toplevel and env.v.LOG:
            builder.start_stdin_log_reader(
                status=opt.status, details=opt.details,
                pretty=env.v.PRETTY, color=env.v.COLOR,
                debug_locks=opt.debug_locks, debug_pids=opt.debug_pids)
        else:
            logs.setup(
                tty=sys.stderr, parent_logs=env.v.LOG,
                pretty=env.v.PRETTY, color=env.v.COLOR)
        if (env.is_toplevel or j > 1) and env.v.LOCKS_BROKEN:
            warn('detected broken fcntl locks; parallelism disabled.\n')
            warn('  ...details: https://github.com/Microsoft/WSL/issues/1927\n')
            if j > 1:
                j = 1

        for t in targets:
            if os.path.exists(t):
                f = state.File(name=t)
                if not f.is_generated:
                    warn(('%s: exists and not marked as generated; ' +
                          'not redoing.\n') % f.nicename())
        state.rollback()

        if j < 0 or j > 1000:
            err('invalid --jobs value: %r\n' % opt.jobs)
        jobserver.setup(j)
        try:
            assert state.is_flushed()
            retcode = builder.run(targets, lambda t: (True, True))
            assert state.is_flushed()
        finally:
            try:
                state.rollback()
            finally:
                try:
                    jobserver.force_return_tokens()
                except Exception, e:  # pylint: disable=broad-except
                    traceback.print_exc(100, sys.stderr)
                    err('unexpected error: %r\n' % e)
                    retcode = 1
        if env.is_toplevel:
            builder.await_log_reader()
        sys.exit(retcode)
    except KeyboardInterrupt:
        if env.is_toplevel:
            builder.await_log_reader()
        sys.exit(200)


if __name__ == '__main__':
    main()
