rm -f pleasefail
redo passfail
if [ ! -e passfail ]; then
	echo "passfail should exist" >&2
	exit 42
fi
PF1=$(cat passfail)
touch pleasefail
if redo passfail 2>/dev/null; then
	echo "redo passfail should have failed" >&2
	exit 42
fi
if [ ! -e passfail ]; then
	echo "passfail should STILL exist" >&2
	exit 42
fi
PF2=$(cat passfail)
if [ "$PF1" != "$PF2" ]; then
	echo "passfail changed even though it failed" >&2
	exit 42
fi
rm -f pleasefail
redo passfail || exit 43
PF3=$(cat passfail)
if [ "$PF1" = "$PF3" ]; then
	echo "passfail did not change even though it passed" >&2
	exit 42
fi
