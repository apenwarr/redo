rm -f t2.count
redo t2
redo t2
OUT=$(cat t2.count | wc -l)
if [ "$OUT" != 2 ]; then
	echo "t2: expected 2"
	exit 43
fi
