#!/bin/sh
fail=0
for d in "$@"; do
	if ! type "$d" >/dev/null 2>/dev/null; then
		echo " -- missing tool: $d" >&2
		fail=1
	fi
done
exit "$fail"
