. ./skip-if-minimal-do.sh
rm -f makedir.log
redo makedir
touch makedir/outfile
./flush-cache.sh
redo-ifchange makedir
COUNT=$(wc -l <makedir.log)
[ "$COUNT" -eq 1 ] || exit 99
