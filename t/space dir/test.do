redo "space file"
F1="$(cat "space 2")"
redo "../space dir/space file"
F2="$(cat "space 2")"
[ "$F1" = "$F2" ] || exit 2
[ -n "$F1" ] || exit 3
