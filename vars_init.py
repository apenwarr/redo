import sys, os, time
import runid

def init(targets):
    if not os.environ.get('REDO'):
        # toplevel call to redo
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

    if not os.environ.get('REDO_STARTDIR'):
        os.environ['REDO_STARTDIR'] = os.getcwd()
        os.environ['REDO_RUNID_FILE'] = 'runid.redo'
        runid.change('runid.redo')
