#!/bin/sh
#echo "Flushing redo cache..." >&2
(
	echo "update Files set checked_runid=null;"
	echo "update Files set changed_runid=changed_runid-1;"
	#echo "update Files set stamp='dirty' where id in (select distinct target from Deps);"
) | sqlite3  "$REDO_BASE/.redo/db.sqlite3"
