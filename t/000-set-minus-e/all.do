rm -f log
redo fatal >&/dev/null || true

[ "$(cat log)" = "ok" ] || exit 5
