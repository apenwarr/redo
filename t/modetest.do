umask 0022
redo mode1
MODE="$(ls -l mode1 | cut -d' ' -f1)"
[ "$MODE" = "-rw-r--r--" ] || exit 78

