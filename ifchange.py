import vars, state, builder, deps
from log import debug, debug2, err


def should_build(f):
    if f.stamp_mtime == 0:
        expect_stamp = None
    else:
        expect_stamp = f.csum or f.stamp
    dirty = deps.isdirty(f, depth='', expect_stamp=expect_stamp,
                         max_runid=vars.RUNID)
    return dirty==[f] and deps.DIRTY or dirty

