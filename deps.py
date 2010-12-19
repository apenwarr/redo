import sys, os
import vars, state, builder
from log import debug

CLEAN = 0
DIRTY = 1

def isdirty(f, depth, max_changed,
            is_checked=state.File.is_checked,
            set_checked=state.File.set_checked_save):
    if vars.DEBUG >= 1:
        debug('%s?%s\n' % (depth, f.nicename()))

    if f.failed_runid:
        debug('%s-- DIRTY (failed last time)\n' % depth)
        return DIRTY
    if f.changed_runid == None:
        debug('%s-- DIRTY (never built)\n' % depth)
        return DIRTY
    if f.changed_runid > max_changed:
        debug('%s-- DIRTY (built)\n' % depth)
        return DIRTY  # has been built more recently than parent
    if is_checked(f):
        if vars.DEBUG >= 1:
            debug('%s-- CLEAN (checked)\n' % depth)
        return CLEAN  # has already been checked during this session
    if not f.stamp:
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return DIRTY

    newstamp = f.read_stamp()
    if f.stamp != newstamp:
        if newstamp == state.STAMP_MISSING:
            debug('%s-- DIRTY (missing)\n' % depth)
        else:
            debug('%s-- DIRTY (mtime)\n' % depth)
        if f.csum:
            return [f]
        else:
            return DIRTY

    must_build = []
    for mode,f2 in f.deps():
        dirty = CLEAN
        if mode == 'c':
            if os.path.exists(os.path.join(vars.BASE, f2.name)):
                debug('%s-- DIRTY (created)\n' % depth)
                dirty = DIRTY
        elif mode == 'm':
            sub = isdirty(f2, depth = depth + '  ',
                          max_changed = max(f.changed_runid,
                                            f.checked_runid),
                          is_checked=is_checked, set_checked=set_checked)
            if sub:
                debug('%s-- DIRTY (sub)\n' % depth)
                dirty = sub
        else:
            assert(mode in ('c','m'))
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
            elif isinstance(dirty,list):
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
    if f.is_override:
        state.warn_override(f.name)
    set_checked(f)
    return CLEAN


