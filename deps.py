import sys, os
import vars, state, builder
from log import debug

class _Clean:
    must_build = ()
    def __nonzero__(self):
        return False
    def __str__(self):
        return "CLEAN"
    def should_build(self, f):
        return self

class _Dirty:
    must_build = ()
    def __init__(self, reason):
        self.reason = reason
    def __nonzero__(self):
        return True
    def __str__(self):
        return "DIRTY(%s)" % (self.reason,)
    def should_build(self, f):
        return self

class DirtyDep:
    must_build = ()
    def __init__(self, dep, reason):
        self.dep = dep
        self.reason = reason
    def __nonzero__(self):
        return True
    def __str__(self):
        return "%s => %s" % (self.dep.name, self.reason)
    def should_build(self, f):
        return self

class Maybe:
    def __init__(self, must_build):
        self.must_build = tuple(must_build)
    def __nonzero__(self):
        return True
    def __str__(self):
        return "MAYBE(must check: %s)" % (", ".join(f.name for f in self.must_build),)
    def should_build(self, f):
        if (f,) == self.must_build:
            return DIRTY_changed
        return self

CLEAN             = _Clean()
DIRTY_failed      = _Dirty("failed last time")
DIRTY_never_built = _Dirty("never built")
DIRTY_built       = _Dirty("newer")
DIRTY_no_stamp    = _Dirty("no stamp")
DIRTY_missing     = _Dirty("missing")
DIRTY_changed     = _Dirty("changed")
DIRTY_created     = _Dirty("created")
DIRTY_forced      = _Dirty("forced")

def isdirty(f, depth, max_changed,
            is_checked=state.File.is_checked,
            set_checked=state.File.set_checked_save):
    if vars.DEBUG >= 1:
        debug('%s?%s\n' % (depth, f.nicename()))

    if f.failed_runid:
        debug('%s-- DIRTY (failed last time)\n' % depth)
        return DIRTY_failed
    if f.changed_runid == None:
        debug('%s-- DIRTY (never built)\n' % depth)
        return DIRTY_never_built
    if f.changed_runid > max_changed:
        debug('%s-- DIRTY (built)\n' % depth)
        return DIRTY_built  # has been built more recently than parent
    if is_checked(f):
        if vars.DEBUG >= 1:
            debug('%s-- CLEAN (checked)\n' % depth)
        return CLEAN  # has already been checked during this session
    if not f.stamp:
        debug('%s-- DIRTY (no stamp)\n' % depth)
        return DIRTY_no_stamp

    newstamp = f.read_stamp()
    if f.stamp != newstamp:
        if newstamp == state.STAMP_MISSING:
            debug('%s-- DIRTY (missing)\n' % depth)
        else:
            debug('%s-- DIRTY (mtime)\n' % depth)
        if f.csum:
            return Maybe((f,))
        elif newstamp == state.STAMP_MISSING:
            return DIRTY_missing
        else:
            return DIRTY_changed

    st = CLEAN
    for mode,f2 in f.deps():
        sub = CLEAN
        if mode == 'c':
            if os.path.exists(os.path.join(vars.BASE, f2.name)):
                debug('%s-- DIRTY (created)\n' % depth)
                sub = DIRTY_created
        elif mode == 'm':
            sub = isdirty(f2, depth = depth + '  ',
                          max_changed = max(f.changed_runid,
                                            f.checked_runid),
                          is_checked=is_checked, set_checked=set_checked)
            if sub:
                debug('%s-- DIRTY (sub)\n' % depth)
        else:
            assert(mode in ('c','m'))
        if sub.must_build:
            # our child f2 might be dirty, but it's not sure yet.
            # It's given us a list of targets we have to redo in order
            # to be sure.
           st = Maybe(st.must_build + sub.must_build)
        elif sub:
            if not f.csum:
                # f is a "normal" target: dirty f2 means f is
                # instantly dirty
                return DirtyDep(f2, sub)
            else:
                # f is "checksummable": dirty f2 means f needs to
                # redo, but f might turn out to be clean after that
                # (ie. our parent might not be dirty).
                return Maybe((f,))

    if st:
        # f is *maybe* dirty because at least one of its children is maybe
        # dirty.  must_build has accumulated a list of "topmost" uncertain
        # objects in the tree.  If we build all those, we can then
        # redo-ifchange f and it won't have any uncertainty next time.
        return st
    debug('%s-- CLEAN\n' % (depth,))

    # if we get here, it's because the target is clean
    if f.is_override:
        state.warn_override(f.name)
    set_checked(f)
    return CLEAN


