import os
from atoi import atoi

if not os.environ.get('REDO'):
    import sys
    sys.stderr.write('%s: error: must be run from inside a .do\n'
                     % sys.argv[0])
    sys.exit(100)

PWD = os.environ.get('REDO_PWD', '')
TARGET = os.environ.get('REDO_TARGET', '')
DEPTH = os.environ.get('REDO_DEPTH', '')
DEBUG = atoi(os.environ.get('REDO_DEBUG', ''))
DEBUG_LOCKS = os.environ.get('REDO_DEBUG_LOCKS', '') and 1 or 0
DEBUG_PIDS = os.environ.get('REDO_DEBUG_PIDS', '') and 1 or 0
OLD_ARGS = os.environ.get('REDO_OLD_ARGS', '') and 1 or 0
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0
XTRACE = os.environ.get('REDO_XTRACE', '') and 1 or 0
KEEP_GOING = os.environ.get('REDO_KEEP_GOING', '') and 1 or 0
SHUFFLE = os.environ.get('REDO_SHUFFLE', '') and 1 or 0
STARTDIR = os.environ.get('REDO_STARTDIR', '')
RUNID = atoi(os.environ.get('REDO_RUNID')) or None
BASE = os.environ['REDO_BASE']
while BASE and BASE.endswith('/'):
    BASE = BASE[:-1]

UNLOCKED = os.environ.get('REDO_UNLOCKED', '') and 1 or 0
os.environ['REDO_UNLOCKED'] = ''  # not inheritable by subprocesses

NO_OOB = os.environ.get('REDO_NO_OOB', '') and 1 or 0
os.environ['REDO_NO_OOB'] = ''    # not inheritable by subprocesses
