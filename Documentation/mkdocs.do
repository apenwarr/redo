redo-ifchange doc.list
xargs redo-ifchange ../mkdocs.yml <doc.list

if type mkdocs >/dev/null 2>/dev/null; then
	(cd .. && mkdocs build)
else
	echo "Warning: mkdocs is missing; can't generate website." >&2
	redo-ifcreate /usr/bin/mkdocs
fi
