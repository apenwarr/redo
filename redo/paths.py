"""Code for manipulating file paths."""
import os
from . import env
from .logs import debug2


def _default_do_files(filename):
    l = filename.split('.')
    for i in range(1, len(l)+1):
        basename = '.'.join(l[:i])
        ext = '.'.join(l[i:])
        if ext:
            ext = '.' + ext
        yield ("default%s.do" % ext), basename, ext


def possible_do_files(t):
    """Yield a list of tuples describing the .do file needed to build t."""
    dirname, filename = os.path.split(t)
    yield (os.path.join(env.v.BASE, dirname), "%s.do" % filename,
           '', filename, '')

    # It's important to try every possibility in a directory before resorting
    # to a parent directory.  Think about nested projects: We don't want
    # ../../default.o.do to take precedence over ../default.do, because
    # the former one might just be an artifact of someone embedding my project
    # into theirs as a subdir.  When they do, my rules should still be used
    # for building my project in *all* cases.
    t = os.path.normpath(os.path.join(env.v.BASE, t))
    dirname, filename = os.path.split(t)
    dirbits = dirname.split('/')
    # since t is an absolute path, dirbits[0] is always '', so we don't
    # need to count all the way down to i=0.
    for i in range(len(dirbits), 0, -1):
        basedir = '/'.join(dirbits[:i])
        subdir = '/'.join(dirbits[i:])
        for dofile, basename, ext in _default_do_files(filename):
            yield (basedir, dofile,
                   subdir, os.path.join(subdir, basename), ext)


def find_do_file(f):
    for dodir, dofile, basedir, basename, ext in possible_do_files(f.name):
        dopath = os.path.join(dodir, dofile)
        debug2('%s: %s:%s ?\n' % (f.name, dodir, dofile))
        if os.path.exists(dopath):
            f.add_dep('m', dopath)
            return dodir, dofile, basedir, basename, ext
        else:
            f.add_dep('c', dopath)
    return None, None, None, None, None
