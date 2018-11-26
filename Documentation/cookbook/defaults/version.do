# Try to get a version number from git, if possible.
if ! git describe >$3; then
    echo "$0: Falling back to static version." >&2
    echo 'UNKNOWN' >$3
fi
redo-always
redo-stamp <$3
