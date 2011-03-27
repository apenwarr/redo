import sys
sys.path.insert(0, '..')
import state

assert(state.relpath('/a/b/c', '/a/b') == 'c')
assert(state.relpath('/a/b/c/', '/a/b') == 'c')
assert(state.relpath('/a/b/c', '/a/b/') == 'c')
assert(state.relpath('/a/b/c//', '/a/b/') == 'c')
assert(state.relpath('/a/b/c/../d', '/a/b/') == 'd')
