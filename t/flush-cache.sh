#!/bin/sh
#echo "Flushing redo cache..." >&2
find "$REDO_BASE/.redo" -name 'built^*' -o -name 'mark^*' |
	xargs rm -f >&2
