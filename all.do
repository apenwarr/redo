if [ "$1,$2" != "all,all" ]; then
	echo "ERROR: old-style redo args detected: don't use --old-args." >&2
	exit 1
fi

# Do this first, to ensure we're using a good shell
redo-ifchange redo/sh

redo-ifchange bin/all docs/all
