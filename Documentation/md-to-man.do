redo-ifchange md2man.py
if ./md2man.py </dev/null >/dev/null 2>/dev/null; then
	echo './md2man.py $1.md.tmp'
else
	(IFS=:; for DIR in $PATH; do redo-ifcreate "$DIR/pandoc"; done)
	echo "Warning: pandoc not installed; can't generate manpages." >&2
	echo 'echo Skipping: $1.1 >&2'
fi
