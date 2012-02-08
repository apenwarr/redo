rm -f log dir1/log dir1/stinky
touch t1.do
../../flush-cache
redo t1
touch t1.do
../../flush-cache
redo t1
../../flush-cache
redo-ifchange t1
C1="$(wc -l <dir1/log)"
C2="$(wc -l <log)"
. ../../skip-if-minimal-do.sh
if [ "$C1" -ne 1 -o "$C2" -ne 2 ]; then
	echo "failed: t1>t1, c1=$C1, c2=$C2" >&2
	exit 55
fi
