import sys, os
import vars, state, builder
from logs import debug

CLEAN = 0
DIRTY = 1

def isdirty(f, depth, max_changed,
            already_checked,
            is_checked=state.File.is_checked,
            set_checked=state.File.set_checked_save):
    if f.id in already_checked:
        raise state.CyclicDependencyError()
    # make a copy of the list, so upon returning, our parent's copy
    # is unaffected
    already_checked = list(already_checked) + [f.id]

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
            if f.stamp and f.is_generated:
                # previously was stamped and generated, but suddenly missing.
                # We can safely forget that it is/was a target; if someone
                # does redo-ifchange on it and it doesn't exist, we'll mark
                # it a target again, but if someone creates it by hand,
                # it'll be a source.  This should reduce false alarms when
                # files change from targets to sources as a project evolves.
                debug('%s   converted target -> source\n' % depth)
                f.is_generated = False
                #f.update_stamp()
                f.save()
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
                          already_checked=already_checked,
                          is_checked=is_checked, set_checked=set_checked)
            if sub:
                debug('%s-- DIRTY (sub)\n' % depth)
                dirty = sub
        else:
            assert(mode in ('c','m'))
        if not f.csum:
            # f is a "normal" target: dirty f2 means f is instantly dirty
            if dirty == DIRTY:
                # f2 is definitely dirty, so f definitely needs to
                # redo.
                return DIRTY
            elif isinstance(dirty,list):
                # our child f2 might be dirty, but it's not sure yet.  It's
                # given us a list of targets we have to redo in order to
                # be sure.
                must_build += dirty
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
    debug('%s-- CLEAN\n' % (depth,))

    # if we get here, it's because the target is clean
    if f.is_override:
        state.warn_override(f.name)
    set_checked(f)
    return CLEAN
