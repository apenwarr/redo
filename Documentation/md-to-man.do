redo-ifchange md2man.py
if ./md2man.py </dev/null >/dev/null; then
	echo './md2man.py $1.md.tmp'
else
	echo "Warning: md2man.py missing modules; can't generate manpages." >&2
	echo "Warning: try this: sudo easy_install markdown BeautifulSoup" >&2
	echo 'echo Skipping: $1.1 >&2'
fi
