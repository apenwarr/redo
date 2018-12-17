redo-ifchange ../../redo/sh
rm -f log
redo fatal >/dev/null 2>&1 || true

[ "$(cat log)" = "ok" ] || exit 5
