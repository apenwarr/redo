import sys, os

def init(targets):
    if not os.environ.get('REDO'):
        # toplevel call to redo
        exenames = [os.path.abspath(sys.argv[0]),
                    os.path.realpath(sys.argv[0])]
        if exenames[0] == exenames[1]:
            exenames = [exenames[0]]
        dirnames = [os.path.dirname(p) for p in exenames]
        os.environ['PATH'] = ':'.join(dirnames) + ':' + os.environ['PATH']
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
