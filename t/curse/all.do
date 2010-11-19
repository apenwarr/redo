redo-ifchange 1.n0 2.n0 3.n0
DEPS=$(seq 10 | sed 's/$/.n1/')
redo-ifchange $DEPS
COUNT=$(cat *.count | wc -l)
if ! [ "$COUNT" = 100 ]; then
	echo "expected 100 writes, got $COUNT" >&2
	exit 42
fi
