if pandoc </dev/null 2>/dev/null; then
	echo 'pandoc -s -r markdown -w man -o $3 $1.md'
else
	echo "Warning: pandoc not installed; can't generate manpages." >&2
	echo 'echo Skipping: $1.1 >&2'
fi
