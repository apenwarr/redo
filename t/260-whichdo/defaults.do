exec >&2

a=$(cd fakesub2 && redo-whichdo d/snork)
# if sh doesn't abort after the above, then it found a .do file as expected

b=$(cat <<EOF
d/snork.do
d/default.do
default.do
EOF
)

if [ "$a" != "$b" ]; then
    printf 'redo-whichdo mismatch.\n\ngot:\n%s\n\nexpected:\n%s\n' "$a" "$b"
    exit 11
fi
