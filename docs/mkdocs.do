redo-ifchange doc.list
xargs redo-ifchange ../mkdocs.yml <doc.list

# Most people don't have mkdocs installed, or are using an obsolete one,
# so let's handle those cases gracefully.
ver=$(mkdocs --version 2>/dev/null | cut -d' ' -f3)
check='
import sys
ok = sys.argv[1].split(".") >= ["1", "0", "4"]
exit(not ok)
'

if ! type mkdocs >/dev/null 2>/dev/null; then
	echo "Warning: mkdocs is missing; can't generate website." >&2
	redo-ifcreate /usr/bin/mkdocs
elif ! python -c "$check" "$ver"; then
	echo "Warning: mkdocs is too old ($ver); need at least 1.0.4." >&2
	mkd=$(which mkdocs 2>/dev/null || :)
	[ -x "$mkd" ] && redo-ifchange "$mkd"
else
	(cd .. && mkdocs build --strict --clean)
fi
