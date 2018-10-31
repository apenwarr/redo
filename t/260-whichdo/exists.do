exec >&2

a=$(cd fakesub && redo-whichdo ../a/b/x.y.z)
# if sh doesn't abort after the above, then it found a .do file as expected

# Note: we expect redo-whichdo to return paths relative to $PWD at the time
# it's run, which in this case is fakesub.
# Likely bugs would be to return paths relative to the start dir, the .redo
# dir, the current target dir, the requested target dir, etc.
b=$(cat <<EOF
../a/b/x.y.z.do
../a/b/default.y.z.do
../a/b/default.z.do
../a/b/default.do
../a/default.y.z.do
../a/default.z.do
../a/default.do
../default.y.z.do
EOF
)

if [ "$a" != "$b" ]; then
    printf 'redo-whichdo mismatch.\n\ngot:\n%s\n\nexpected:\n%s\n' "$a" "$b"
    exit 11
fi
