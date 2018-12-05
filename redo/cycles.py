"""Code for detecting and aborting on cyclic dependency loops."""
import os


class CyclicDependencyError(Exception):
    pass


def _get():
    """Get the list of held cycle items."""
    return os.environ.get('REDO_CYCLES', '').split(':')


def add(fid):
    """Add a lock to the list of held cycle items."""
    items = set(_get())
    items.add(str(fid))
    os.environ['REDO_CYCLES'] = ':'.join(list(items))


def check(fid):
    if str(fid) in _get():
        # Lock already held by parent: cyclic dependency
        raise CyclicDependencyError()
