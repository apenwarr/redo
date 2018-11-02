rm -rf sub.tmp sub2.tmp sub3.tmp

redo-ifchange sub.tmp/test.txt
[ -e sub.tmp/test.txt ] || exit 96

redo-ifchange sub2.tmp/a/b/c/test.txt
[ -e sub2.tmp/a/b/c/test.txt ] || exit 97

mkdir -p sub3.tmp/a
redo-ifchange sub3.tmp/a/b/c/test.txt
[ -e sub2.tmp/a/b/c/test.txt ] || exit 98
