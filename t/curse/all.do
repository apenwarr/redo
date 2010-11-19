rm -f in.countall out.countall *.count
touch in.countall out.countall
echo x >x.count
redo-ifchange 1.n0 2.n0 3.n0
DEPS=$(seq 10 | sed 's/$/.n1/')
redo-ifchange $DEPS
COUNT_IN=$(ls *.count | wc -l)
COUNT_OUT=$(cat *.count | wc -l)
if [ "$COUNT_IN" != "$COUNT_OUT" ]; then
	echo "expected $COUNT_IN individual writes, got $COUNT_OUT" >&2
	exit 42
fi
COUNTALL_IN=$(cat in.countall | wc -l)
COUNTALL_OUT=$(cat out.countall | wc -l)
if [ "$COUNTALL_IN" != "$COUNTALL_OUT" ]; then
	echo "expected $COUNTALL_IN allwrites, got $COUNTALL_OUT" >&2
	exit 43
fi
