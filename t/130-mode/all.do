umask 0022
redo mode1
MODE="$(stat -c %A mode1)"
[ "$MODE" = "-rw-r--r--" ] || exit 78

