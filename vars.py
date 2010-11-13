import os

REDO_TARGET = os.environ.get('REDO_TARGET', '')
REDO_DEPTH = os.environ.get('REDO_DEPTH', '')
REDO_DEBUG = os.environ.get('REDO_DEBUG', '') and 1 or 0
REDO_VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0
REDO_BASE = os.path.abspath(os.environ['REDO_BASE'])
while REDO_BASE.endswith('/'):
    REDO_BASE = REDO_BASE[:-1]
