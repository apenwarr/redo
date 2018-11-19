if type cc >/dev/null 2>&1; then
	redo-ifchange hello
else
	echo "$0: No C compiler installed; skipping this test." >&2
	redo-ifcreate /usr/bin/cc
fi
