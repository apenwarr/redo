if redo-ifchange broken 2>/dev/null; then
	echo "expected broken.do to fail, but it didn't" >&2
	exit 44
fi
