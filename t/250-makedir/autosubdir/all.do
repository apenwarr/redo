rm -rf sub.tmp
redo-ifchange sub.tmp/test.txt
[ -e sub.tmp/test.txt ] || exit 96
