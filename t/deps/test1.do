# force-rebuild t1dep
redo t1dep

if [ -e t1a ]; then
	BEFORE="$(cat t1a)"
else
	BEFORE=
fi
../flush-cache
redo-ifchange t1a  # it definitely had to rebuild because t1dep changed
AFTER="$(cat t1a)"
if [ "$BEFORE" = "$AFTER" ]; then
	echo "t1a was not rebuilt!" >&2
	exit 43
fi
