import os
import atoi

TARGET = os.environ.get('REDO_TARGET', '')
DEPTH = os.environ.get('REDO_DEPTH', '')
DEBUG = atoi.atoi(os.environ.get('REDO_DEBUG', ''))
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0
SHUFFLE = os.environ.get('REDO_SHUFFLE', '') and 1 or 0
STARTDIR = os.environ.get('REDO_STARTDIR', '')
BASE = os.environ.get('REDO_BASE', '')
if BASE:
    BASE = os.path.abspath(BASE)
    while BASE and BASE.endswith('/'):
        BASE = BASE[:-1]
