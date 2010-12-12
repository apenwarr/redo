if [ -n "$DO_BUILT" ]; then
	echo "$REDO_TARGET: skipping: not supported in minimal/do." >&2
	exit 0
fi

