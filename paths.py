import os
import vars
from logs import err, debug2


def _default_do_files(filename):
    l = filename.split('.')
    for i in range(1,len(l)+1):
        basename = '.'.join(l[:i])
        ext = '.'.join(l[i:])
        if ext: ext = '.' + ext
        yield ("default%s.do" % ext), basename, ext

def possible_do_files(t):
    """
        For a given target (t), generate each possible dofile, regardless of
        its current existence.  (This lets us easily add create dependencies
        on the missing files up to the first one we find!)

        Elements of the generated stream are 5-tuples:

            dodir     -- absolute directory containing the .do file
            dofile    -- name of the .do file (in dodir)
            basedir   -- target's directory, relative to dodir
            basename  -- target's base name, stripped of its extension
            extension -- target's extension, if defaulting, or '', if not
    """

    dirname,filename = os.path.split(t)
    d = os.path.join(vars.BASE, dirname)
    dofile = "%s.do" % filename

    # Look for this specific target's dofile in do/ and .
    yield (d, os.path.join("do", dofile), '', filename, '')
    yield (d,                    dofile , '', filename, '')

    # It's important to try every possibility in a directory before resorting
    # to a parent directory.  Think about nested projects: We don't want
    # ../../default.o.do to take precedence over ../default.do, because
    # the former one might just be an artifact of someone embedding my project
    # into theirs as a subdir.  When they do, my rules should still be used
    # for building my project in *all* cases.
    t = os.path.normpath(os.path.join(vars.BASE, t))
    dirname,_ = os.path.split(t)
    dirbits = dirname.split('/')
    # since t is an absolute path, dirbits[0] is always '', so we don't
    # need to count all the way down to i=0.
    for i in range(len(dirbits), 0, -1):
        basedir = '/'.join(dirbits[:i])
        subdir = '/'.join(dirbits[i:])

        # If we have ascended, look for the specific target hierarchically in
        # our current dodir (that is, for "subdir/target", look for
        # "do/subdir/target.do"
        if subdir != "" :
            yield (basedir, os.path.join("do", os.path.join(subdir, dofile)),
                            '', os.path.join(subdir, filename), '')

        # Look for defaults in our dodir
        for j in range(len(dirbits), i-1, -1):
            for defdofile,basename,ext in _default_do_files(filename):
                yield (basedir,
                        os.path.join("do",
                            os.path.join('/'.join(dirbits[i:j]), defdofile)),
                       subdir, os.path.join(subdir, basename), ext)

        # Look for defaults in the current directory
        for defdofile,basename,ext in _default_do_files(filename):
            yield (basedir, defdofile,
                   subdir, os.path.join(subdir, basename), ext)


def find_do_file(f):
    for dodir,dofile,basedir,basename,ext in possible_do_files(f.name):
        dopath = os.path.join(dodir, dofile)
        debug2('%s: %s:%s ?\n' % (f.name, dodir, dofile))
        if os.path.exists(dopath):
            f.add_dep('m', dopath)
            return dodir,dofile,basedir,basename,ext
        else:
            f.add_dep('c', dopath)
    return None,None,None,None,None
