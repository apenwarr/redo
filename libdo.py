import sys, os
import vars

def relpath(t, base):
    t = os.path.abspath(t)
    tparts = t.split('/')
    bparts = base.split('/')
    for tp,bp in zip(tparts,bparts):
        if tp != bp:
            break
        tparts.pop(0)
        bparts.pop(0)
    while bparts:
        tparts.insert(0, '..')
        bparts.pop(0)
    return '/'.join(tparts)


def sname(typ, t):
    # FIXME: t.replace(...) is non-reversible and non-unique here!
    tnew = relpath(t, vars.BASE)
    #log('sname: (%r) %r -> %r\n' % (vars.BASE, t, tnew))
    return vars.BASE + ('/.redo/%s^%s' % (typ, tnew.replace('/', '^')))


def add_dep(t, mode, dep):
    open(sname('dep', t), 'a').write('%s %s\n' % (mode, dep))
