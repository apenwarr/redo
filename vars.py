import os

REDO_TARGET = os.getenv('REDO_TARGET', '')
REDO_DEPTH = os.getenv('REDO_DEPTH', '')
REDO_DEBUG = os.getenv('REDO_DEBUG', '') and 1 or 0
REDO_VERBOSE = os.getenv('REDO_VERBOSE', '') and 1 or 0
REDO_BASE = os.path.abspath(os.getenv('REDO_BASE', ''))
while REDO_BASE.endswith('/'):
    REDO_BASE = REDO_BASE[:-1]
