import vars, state, builder, deps
from log import debug, debug2, err


def should_build(f):
    if f.stamp_mtime >= vars.RUNID and f.exitcode:
        raise Exception('earlier build of %r failed with code %d'
                        % (f.name, f.exitcode))
    if f.stamp_mtime == 0:
        expect_stamp = None
    else:
        expect_stamp = f.csum or f.stamp
    dirty = deps.isdirty(f, depth='', expect_stamp=expect_stamp,
                         max_runid=vars.RUNID)
    return dirty==[f] and deps.DIRTY or dirty


def build_ifchanged(sf):
    dirty = should_build(sf)
    while dirty and dirty != deps.DIRTY:
        # FIXME: bring back the old (targetname) notation in the output
        #  when we need to do this.  And add comments.
        for t2 in dirty:
            rv = build_ifchanged(t2)
            if rv:
                return rv
        dirty = should_build(sf)
        #assert(dirty in (deps.DIRTY, deps.CLEAN))
    if dirty:
        rv = builder.build(sf)
        if rv:
            return rv
    return 0
