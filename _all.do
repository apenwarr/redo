if [ "$1,$2" != "_all,_all" ]; then
	echo "ERROR: old-style redo args detected: don't use --old-args." >&2
	exit 1
fi

redo-ifchange redo-sh.dir
redo-ifchange version/all Documentation/all
