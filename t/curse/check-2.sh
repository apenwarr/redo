COUNT_IN=$(ls *.count | wc -l)
COUNT_OUT=$(cat *.count | wc -l)
if [ "$COUNT_IN" -ne "$COUNT_OUT" ]; then
	echo "expected $COUNT_IN individual writes, got $COUNT_OUT" >&2
	exit 42
fi
COUNTALL_IN=$(cat in.countall | wc -l)
COUNTALL_OUT=$(cat out.countall | wc -l)
if [ "$COUNTALL_IN" -ne "$COUNTALL_OUT" ]; then
	echo "expected $COUNTALL_IN allwrites, got $COUNTALL_OUT" >&2
	exit 43
fi
