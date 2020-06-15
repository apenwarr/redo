# This test is meant to confirm some basic redo functionality
# related to static files not in the build tree. But if your
# system doesn't happen to have stdio.h in the usual location,
# let's not explode just for that.
stdio=/usr/include/stdio.h
[ -e "$stdio" ] || stdio=

redo-ifchange CC hello.c $stdio
redo-ifcreate stdio.h
../sleep 3
./CC hello.c
