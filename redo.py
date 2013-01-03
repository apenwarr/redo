#!/usr/bin/env python
import sys, os
import options
from helpers import atoi

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are read from .do files (variables intact)
x,xtrace   print commands as they are executed (variables expanded)
k,keep-going  keep going as long as possible even if some targets fail
overwrite  overwrite files even if generated outside of redo
shuffle    randomize the build order to find dependency bugs
debug-locks  print messages about file locking (useful for debugging)
debug-pids   print process ids as part of log messages (useful for debugging)
version    print the current version and exit
old-args   use old-style definitions of $1,$2,$3 (deprecated)
main=      Choose which redo flavour to execute
"""

def read_opts():
    o = options.Options(optspec)
    (opt, flags, extra) = o.parse(sys.argv[1:])

    redo_flavour = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    targets = extra

    if opt.overwrite:
        os.environ['REDO_OVERWRITE'] = '1'
    if opt.version:
        import version
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
    if opt.old_args:
        os.environ['REDO_OLD_ARGS'] = '1'
    if opt.main:
        redo_flavour = opt.main

    return atoi(opt.jobs or 1), redo_flavour, targets

def set_main(arg0):
    # When the module is imported, change the process title.
    # We do it here because this module is imported by all the scripts.
    try:
      	from setproctitle import setproctitle
    except ImportError:
      	pass
    else:
      	setproctitle(" ".join([arg0].extend(sys.argv[1:])))


def init(targets, redo_binaries=[]):
    import time
    import runid
    if not os.environ.get('REDO'):
        if len(targets) == 0:
            targets.append('all')

        # create the bin dir
        bindir = os.path.join(os.getcwd(), ".redo", "bin")
        try: os.makedirs(bindir)
        except: pass
        main = os.path.realpath(sys.argv[0])
        for exe in redo_binaries:
            exe = os.path.join(bindir, exe)
            try: os.unlink(exe)
            except: pass
            os.symlink(main, exe)
        os.environ['PATH'] = bindir + ":" + os.environ['PATH']
        os.environ['REDO'] = os.path.join(bindir, "redo")

    if not os.environ.get('REDO_STARTDIR'):
        os.environ['REDO_STARTDIR'] = os.getcwd()
        os.environ['REDO_RUNID_FILE'] = '.redo/runid'
        runid.change('.redo/runid')

if __name__ == '__main__':
    try:
        from main import mains
        jobs, redo_flavour, targets = read_opts()
        init(targets, mains.keys())
        from log import err, debug
        import jwack

        if not redo_flavour.startswith("redo"):
            redo_flavour = "redo-%s" % redo_flavour
        if redo_flavour not in mains:
            err("invalid redo: %s\n", redo_flavour)
            sys.exit(1)

        set_main(redo_flavour)
        
        if jobs < 1 or jobs > 1000:
            err('invalid --jobs value: %r\n', opt.jobs)
        jwack.setup(jobs)
        
        debug("%s %r\n", redo_flavour, targets)
        sys.exit(mains[redo_flavour](redo_flavour, targets) or 0)
    except KeyboardInterrupt:
        sys.exit(200)
