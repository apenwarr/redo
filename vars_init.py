import sys, os


is_toplevel = False


def init_no_state():
    if not os.environ.get('REDO'):
        os.environ['REDO'] = 'NOT_DEFINED'
        is_toplevel = True
    if not os.environ.get('REDO_BASE'):
        os.environ['REDO_BASE'] = 'NOT_DEFINED'


def init(targets):
    if not os.environ.get('REDO'):
        # toplevel call to redo
        global is_toplevel
        is_toplevel = True
        if len(targets) == 0:
            targets.append('all')
        exenames = [os.path.abspath(sys.argv[0]),
                    os.path.realpath(sys.argv[0])]
        dirnames = [os.path.dirname(p) for p in exenames]
        trynames = ([os.path.abspath(p+'/../lib/redo') for p in dirnames] +
                    [p+'/redo-sh' for p in dirnames] +
                    dirnames)
        seen = {}
        dirs = []
        for k in trynames:
            if not seen.get(k):
                seen[k] = 1
                dirs.append(k)
        os.environ['PATH'] = ':'.join(dirs) + ':' + os.environ['PATH']
        os.environ['REDO'] = os.path.abspath(sys.argv[0])

    if not os.environ.get('REDO_BASE'):
        base = os.path.commonprefix([os.path.abspath(os.path.dirname(t))
                                     for t in targets] + [os.getcwd()])
        bsplit = base.split('/')
        for i in range(len(bsplit)-1, 0, -1):
            newbase = '/'.join(bsplit[:i])
            if os.path.exists(newbase + '/.redo'):
                base = newbase
                break
        os.environ['REDO_BASE'] = base
        os.environ['REDO_STARTDIR'] = os.getcwd()

        import state
        state.init()

    os.environ['REDO_LOCKS'] = os.environ.get('REDO_LOCKS', '')
