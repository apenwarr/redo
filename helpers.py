import sys, os, errno


def log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()


def unlink(f):
    """Delete a file at path 'f' if it currently exists.

    Unlike os.unlink(), does not throw an exception if the file didn't already
    exist.
    """
    try:
        os.unlink(f)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass  # it doesn't exist, that's what you asked for


