#!/bin/sh
#echo "Flushing redo cache..." >&2
if [ -z "$DO_BUILT" ]; then
	(
		echo ".timeout 5000"
		echo "pragma synchronous = off;"
		echo "update Files set checked_runid=checked_runid-1, " \
		     "       changed_runid=changed_runid-1, " \
		     "       failed_runid=failed_runid-1;"
	) | sqlite3  "$REDO_BASE/.redo/db.sqlite3"
fi

