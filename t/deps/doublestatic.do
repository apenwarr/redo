rm -f static.log

redo static1 static2

touch static.in
../flush-cache
redo-ifchange static1 static2

COUNT=$(wc -l <static.log)
. ../skip-if-minimal-do.sh
[ "$COUNT" -eq 4 ] || exit 55
