exec >&2
redo-ifchange ../redo/version/all ../redo/python list redo-sh
xargs redo-ifchange <list
