"""Code for manipulating the Unix process title."""
import os, sys

# FIXME: setproctitle module is only usable if *not* using python -S,
# and without -S, python startup time is annoyingly longer
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(name):
        pass


def auto():
    """Automatically clean up the title as seen by 'ps', based on argv."""
    exe = sys.argv[0]
    exename, ext = os.path.splitext(os.path.basename(sys.argv[0]))
    title = ' '.join([exename] + sys.argv[1:])
    setproctitle(title)
