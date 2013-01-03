import os
from atoi import atoi
import runid


if not os.environ.get('REDO'):
    import sys
    sys.stderr.write('%s: error: must be run from inside a .do\n'
                     % sys.argv[0])
    sys.exit(100)

# The absolute path that was os.getcwd() when we started.
STARTDIR = os.environ.get('REDO_STARTDIR', '')

# A user-friendly printable version of os.getcwd() (ie. the location of the
# currently running .do file) relative to STARTDIR.
# For example, ../foo/blah
# This is better to use than os.path.relpath, because your paths might include
# symlinks that make a/b/../c not equal to a/c.
PWD = os.environ.get('REDO_PWD', '')

# The path to the target currently being built, relative to PWD.
TARGET = os.environ.get('REDO_TARGET', '')

# The depth of redo recursion, in the form of a string of space characters.
# The deeper we go, the more space characters we append.
DEPTH = os.environ.get('REDO_DEPTH', '')

# The value of the --overwrite flag.
OVERWRITE = os.environ.get('REDO_OVERWRITE', '') and 1 or 0

# The value of the -d flag.
DEBUG = atoi(os.environ.get('REDO_DEBUG', ''))

# The value of the --debug-pids flag.
DEBUG_PIDS = os.environ.get('REDO_DEBUG_PIDS', '') and 1 or 0

# The value of the --old-args flag.
OLD_ARGS = os.environ.get('REDO_OLD_ARGS', '') and 1 or 0

# The value of the -v flag.
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0

# The value of the -x flag.
XTRACE = os.environ.get('REDO_XTRACE', '') and 1 or 0

# The value of the -k flag.
KEEP_GOING = os.environ.get('REDO_KEEP_GOING', '') and 1 or 0

# The value of the --shuffle flag.
SHUFFLE = os.environ.get('REDO_SHUFFLE', '') and 1 or 0

# The id of the current redo execution; an int(time.time()) value.
RUNID_FILE = os.environ.get('REDO_RUNID_FILE')
RUNID = runid.read(os.path.join(STARTDIR, RUNID_FILE))
