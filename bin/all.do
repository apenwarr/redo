exec >&2
redo-ifchange ../redo/version/all ../redo/py ../redo/sh list
xargs redo-ifchange <list
