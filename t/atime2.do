# make sure redo doesn't think merely *reading* the old file counts as
# modifying it in-place.
cat $1 >/dev/null 2>/dev/null || true
./tick
cat $1 >/dev/null 2>/dev/null || true
echo hello
