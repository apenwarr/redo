import sys, os
import vars, state, builder
from log import debug, debug2, debug3, warn

CLEAN = 0
DIRTY = 1

# FIXME: sanitize the return values of this function into a tuple instead.
# FIXME: max_runid is probably the wrong concept.
def isdirty(f, depth, expect_stamp, max_runid):
    debug('%s?%s\n', depth, f.name)

    if not f.is_generated and not expect_stamp and f.exists():
        debug('%s-- CLEAN (static)\n', depth)
        return CLEAN
    if f.exitcode:
        debug('%s-- DIRTY (failed last time)\n', depth)
        return DIRTY
    if not state.is_missing(expect_stamp) and state.is_missing(f.stamp):
        debug('%s-- DIRTY (never built)\n', depth)
        return DIRTY
    if f.stamp_mtime > max_runid:
        debug('%s-- DIRTY (built)\n', depth)
        return DIRTY
    if f.stamp_mtime >= vars.RUNID:
        debug('%s-- CLEAN (checked)\n', depth)
        return CLEAN  # has already been checked during this session
    if not f.stamp:
        debug('%s-- DIRTY (no stamp)\n', depth)
        return DIRTY

    newstamp = f.read_stamp()

    debug3('%sexpect: %s\n', depth, expect_stamp)
    debug3('%sold:    %s\n', depth, f.stamp)
    debug3('%snew:    %s\n', depth, newstamp)
    if f.csum: debug3('%scsum:   %s\n', depth, f.csum)

    if f.is_generated and newstamp != f.stamp and not state.is_missing(newstamp):
        if vars.OVERWRITE:
            debug('%s-- DIRTY (override)\n', depth)
            return DIRTY
        else:
            debug('%s-- CLEAN (override)\n', depth)
            return CLEAN

    if newstamp != f.stamp:
        if state.is_missing(newstamp):
            debug('%s-- DIRTY (missing)\n', depth)
        else:
            debug('%s-- DIRTY (mtime)\n', depth)
        return [f] if f.csum else DIRTY

    must_build = []
    for stamp2, f2 in f.deps:
        dirty = CLEAN
        f2 = state.File(f2, f.dir)
        sub = isdirty(f2, depth = depth + '  ',
                      expect_stamp = stamp2,
                      max_runid = max(f.stamp_mtime, vars.RUNID))
        if sub:
            debug('%s-- DIRTY (sub)\n', depth)
            dirty = sub
        if not f.csum:
            # f is a "normal" target: dirty f2 means f is instantly dirty
            if dirty:
                # if dirty==DIRTY, this means f is definitely dirty.
                # if dirty==[...], it's a list of the uncertain children.
                return dirty
        else:
            # f is "checksummable": dirty f2 means f needs to redo,
            # but f might turn out to be clean after that (ie. our parent
            # might not be dirty).
            if dirty == DIRTY:
                # f2 is definitely dirty, so f definitely needs to
                # redo.  However, after that, f might turn out to be
                # unchanged.
                return [f]
            elif isinstance(dirty, list):
                # our child f2 might be dirty, but it's not sure yet.  It's
                # given us a list of targets we have to redo in order to
                # be sure.
                must_build += dirty

    if must_build:
        # f is *maybe* dirty because at least one of its children is maybe
        # dirty.  must_build has accumulated a list of "topmost" uncertain
        # objects in the tree.  If we build all those, we can then
        # redo-ifchange f and it won't have any uncertainty next time.
        return must_build

    if expect_stamp != (f.csum or f.stamp):
        # This must be after we checked the children. Before, we didn't knew
        # if the current target was dirty or not
        debug('%s-- DIRTY (parent)\n', depth)
        return DIRTY

    # if we get here, it's because the target is clean
    debug2('%s-- CLEAN (dropped off)\n', depth)
    return CLEAN


