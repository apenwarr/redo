import sys, os
import vars, state, builder
from log import debug, debug2, debug3, warn

CLEAN = 0
DIRTY = 1

# FIXME: sanitize the return values of this function into a tuple instead.
# FIXME: max_runid is probably the wrong concept.
def isdirty(f, depth, expect_stamp, max_runid,
            is_checked=lambda x: False,  #FIXME
            set_checked=lambda y: None):  #FIXME
    if vars.DEBUG >= 1:
        debug('%s?%s\n' % (depth, f.nicename()))

    if not f.is_generated and not expect_stamp and f.exists():
        debug('%s-- CLEAN (static)\n' % depth)
        return CLEAN
    if f.exitcode:
        debug('%s-- DIRTY (failed last time)\n' % depth)
        return DIRTY
    if not state.is_missing(expect_stamp) and state.is_missing(f.stamp):
        debug('%s-- DIRTY (never built)\n' % depth)
        return DIRTY
    if f.stamp_mtime > max_runid:
        debug('%s-- DIRTY (built)\n' % depth)
        return DIRTY
    if is_checked(f) or f.stamp_mtime >= vars.RUNID:
        debug('%s-- CLEAN (checked)\n' % depth)
        return CLEAN  # has already been checked during this session
    if not f.stamp:
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return DIRTY

    newstamp = f.csum_or_read_stamp()
    debug3('%r\n expect=%r\n    old=%r\n    new=%r\n'
           % (f.name, expect_stamp, f.csum or f.stamp, newstamp))
    if expect_stamp != newstamp:
        if state.is_missing(newstamp):
            debug('%s-- DIRTY (missing)\n' % depth)
        else:
            debug('%s-- DIRTY (mtime)\n' % depth)
        if f.csum:
            return [f]
        else:
            return DIRTY

    must_build = []
    for stamp2, f2 in f.deps:
        dirty = CLEAN
        f2 = state.File(name=f2, parent=f)
        sub = isdirty(f2, depth = depth + '  ',
                      expect_stamp = stamp2,
                      max_runid = max(f.stamp_mtime, vars.RUNID),
                      is_checked=is_checked, set_checked=set_checked)
        if sub:
            debug('%s-- DIRTY (sub)\n' % depth)
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

    # if we get here, it's because the target is clean
    debug2('%s-- CLEAN (dropped off)\n' % depth)
    newstamp = f.read_stamp()
    if f.stamp != newstamp and not state.is_missing(newstamp):
        warn('%r != %r\n' % (f.stamp, newstamp))
        state.warn_override(f.name)
    set_checked(f)
    return CLEAN


