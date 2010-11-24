redo chdir1
redo chdir2
rm -f chdir1
. ./flush-cache.sh

# chdir2 sets its dependency on chdir1 in an odd way, so this might fail if
# redo doesn't catch it
redo-ifchange chdir2
[ -e chdir1 ] || exit 77
