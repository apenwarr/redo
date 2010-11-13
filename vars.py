import os

TARGET = os.environ.get('REDO_TARGET', '')
DEPTH = os.environ.get('REDO_DEPTH', '')
DEBUG = os.environ.get('REDO_DEBUG', '') and 1 or 0
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0
BASE = os.environ.get('REDO_BASE', '')
if BASE:
    BASE = os.path.abspath(BASE)
    while BASE and BASE.endswith('/'):
        BASE = BASE[:-1]
