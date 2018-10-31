exec >&2

# Testing the search path for non-existent do files is a little tricky.
# We can't be sure where our current directory is, so we don't know how
# far up the stack redo will need to search.
#
# To dodge the problem, let's "cd /" first so that we're testing a target
# relative to a known location (the root directory).

if [ -e '/default.do' -o \
     -e '/default.z.do' -o \
     -e '/default.y.z.do' ]; then
    echo "Weird: /default.*.do exists; can't run this test."
    exit 99
fi

# redo-whichdo *should* fail here, so don't abort the script for that.
set +e
a=$(cd / && redo-whichdo __nonexist/a/x.y.z)
rv=$?
set -e

if [ "$rv" -eq 0 ]; then
    echo "redo-whichdo should return nonzero for a missing .do file."
    exit 10
fi

b=$(cat <<EOF
__nonexist/a/x.y.z.do
__nonexist/a/default.y.z.do
__nonexist/a/default.z.do
__nonexist/a/default.do
__nonexist/default.y.z.do
__nonexist/default.z.do
__nonexist/default.do
default.y.z.do
default.z.do
default.do
EOF
)

if [ "$a" != "$b" ]; then
    printf 'redo-whichdo mismatch.\n\ngot:\n%s\n\nexpected:\n%s\n' "$a" "$b"
    exit 11
fi
