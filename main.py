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

def main_redo(redo_flavour, targets):
    import vars, state, builder

    any_errors = 0

    targets = state.fix_chdir(targets)
    for t in targets:
        f = state.File(t)
        retcode = builder.build(t)
        any_errors += retcode
        if retcode and not vars.KEEP_GOING:
            return retcode
    if any_errors:
        return 1

def main_redo_ifchange(redo_flavour, targets):
    import ifchange, state, vars
    from log import debug2

    retcode = 202
    any_errors = 0

    targets = state.fix_chdir(targets)
    if vars.TARGET:
        f = state.File(name=vars.TARGET)
        debug2('TARGET: %r %r %r\n', vars.STARTDIR, vars.PWD, vars.TARGET)
    else:
        f = me = None
        debug2('redo-ifchange: no target - not adding depends.\n')

    retcode = 0
    for t in targets:
        sf = state.File(name=t)
        retcode = ifchange.build_ifchanged(sf)
        any_errors += retcode
        if f:
            sf.refresh()
            f.add_dep(sf)
        if retcode and not vars.KEEP_GOING:
            return retcode
    if any_errors:
        return 1

def main_redo_ifcreate(redo_flavour, targets):
    import vars, state
    from log import err

    targets = state.fix_chdir(targets)
    f = state.File(vars.TARGET)
    for t in targets:
        if os.path.exists(t):
            err('%s: error: %r already exists\n', redo_flavour, t)
            return 1
        else:
            f.add_dep(state.File(name=t))

def main_redo_always(redo_flavour, targets):
    import vars, state

    state.fix_chdir([])
    f = state.File(vars.TARGET)
    f.add_dep(state.File(name=state.ALWAYS))

def main_redo_stamp(redo_flavour, targets):
    import vars, state
    
    if len(targets) > 1:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    if os.isatty(0):
        err('%s: you must provide the data to stamp on stdin\n', redo_flavour)
        return 1

    # hashlib is only available in python 2.5 or higher, but the 'sha' module
    # produces a DeprecationWarning in python 2.6 or higher.  We want to support
    # python 2.4 and above without any stupid warnings, so let's try using hashlib
    # first, and downgrade if it fails.
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
        if not b: break

    csum = sh.hexdigest()

    if not vars.TARGET:
        return 0

    state.fix_chdir([])
    f = state.File(vars.TARGET)
    f._add('%s .' % csum)

def main_redo_ood(redo_flavour, targets):
    import vars, state, deps
    from log import err

    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.is_generated and f.exists():
            if deps.isdirty(f, depth='', max_runid=vars.RUNID,
                            expect_stamp=f.stamp):
                print f.name

def main_redo_sources(redo_flavour, targets):
    import state
    from log import err

    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.name.startswith('//'):
            continue  # special name, ignore
        if not f.is_generated and f.exists():
            print f.name

def main_redo_targets(redo_flavour, targets):
    import state
    from log import err

    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.is_generated and f.exists():
            print f.name

mains = {
    'redo-sources':  main_redo_sources,
    'redo-targets':  main_redo_targets,
    'redo-ood':      main_redo_ood,
    'redo-stamp':    main_redo_stamp,
    'redo-always':   main_redo_always,
    'redo-ifcreate': main_redo_ifcreate,
    'redo-ifchange': main_redo_ifchange,
    'redo':          main_redo}

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
        jobs, redo_flavour, targets = read_opts()
        init(targets, mains.keys())
        from log import err, debug

        if not redo_flavour.startswith("redo"):
            redo_flavour = "redo-%s" % redo_flavour
        if redo_flavour not in mains:
            err("invalid redo: %s\n", redo_flavour)
            sys.exit(1)

        set_main(redo_flavour)
        
        if jobs < 1 or jobs > 1000:
            err('invalid --jobs value: %r\n', opt.jobs)
        
        debug("%s %r\n", redo_flavour, targets)
        sys.exit(mains[redo_flavour](redo_flavour, targets) or 0)
    except KeyboardInterrupt:
        sys.exit(200)
