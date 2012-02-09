exec >&2
. ../skip-if-minimal-do.sh

rm -f out.log sort.log err.log
redo --keep-going 1.ok 2.fail 3.fail 4.ok 5.ok 6.fail 7.ok >&err.log &&
   exit 11  # expect it to return nonzero due to failures
sort out.log >sort.log

expect="1
2 fail
3 fail
4
5
6 fail
7"

[ "$(cat sort.log)" = "$expect" ] || exit 22
