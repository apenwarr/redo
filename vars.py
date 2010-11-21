import os
import atoi

PWD = os.environ.get('REDO_PWD', '')
TARGET = os.environ.get('REDO_TARGET', '')
DEPTH = os.environ.get('REDO_DEPTH', '')
DEBUG = atoi.atoi(os.environ.get('REDO_DEBUG', ''))
DEBUG_LOCKS = os.environ.get('REDO_DEBUG_LOCKS', '') and 1 or 0
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0
XTRACE = os.environ.get('REDO_XTRACE', '') and 1 or 0
KEEP_GOING = os.environ.get('REDO_KEEP_GOING', '') and 1 or 0
SHUFFLE = os.environ.get('REDO_SHUFFLE', '') and 1 or 0
STARTDIR = os.environ['REDO_STARTDIR']
BASE = os.environ['REDO_BASE']
while BASE and BASE.endswith('/'):
    BASE = BASE[:-1]
