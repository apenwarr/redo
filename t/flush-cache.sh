#!/bin/sh
#echo "Flushing redo cache..." >&2
(
	echo ".timeout 5000"
	echo "pragma synchronous = off;"
	echo "update Files set checked_runid=null, " \
	     "       changed_runid=changed_runid-1, " \
	     "       failed_runid=failed_runid-1;"
) | sqlite3  "$REDO_BASE/.redo/db.sqlite3"
