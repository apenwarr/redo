exec >&2
rm -f bork.do bork bork.log sub sub.log targets.out

qgrep() {
	# like "grep -q", but portable
	grep "$@" >/dev/null
}

cp bork.do.in bork.do
redo bork
[ "$(cat bork.log)" = "x" ] || exit 2
redo bork
[ "$(cat bork.log)" = "xx" ] || exit 3

redo-ifchange sub
[ "$(cat bork.log)" = "xx" ] || exit 10
[ "$(cat sub.log)" = "y" ] || exit 11
. ../skip-if-minimal-do.sh
redo-sources | qgrep '^bork$' && exit 12
redo-targets | tee targets.out | qgrep '^bork$' || exit 13

# Might as well test redo-ood while we're here
../flush-cache
redo bork
redo-targets | qgrep '^bork$' || exit 15
redo-targets | qgrep '^sub$'  || exit 16
redo-ood     | qgrep '^sub$'  || exit 17

redo-ifchange sub
[ "$(cat bork.log)" = "xxx" ] || exit 18
[ "$(cat sub.log)" = "yy" ] || exit 19

rm -f bork
../flush-cache
redo-ifchange sub  # rebuilds, and sub.do drops dependency on bork
[ "$(cat bork.log)" = "xxx" ] || exit 20
[ "$(cat sub.log)" = "yyy" ] || exit 21
redo-sources | qgrep '^bork$' && exit 22  # nonexistent, so not a source
redo-targets | qgrep '^bork$' && exit 23  # deleted; not a target anymore

echo static >bork
../flush-cache
redo-ifchange sub  # doesn't depend on bork anymore, so doesn't rebuild
[ "$(cat bork.log)" = "xxx" ] || exit 30
[ "$(cat sub.log)" = "yyy" ] || exit 31

# bork should now be considered static, so no warning or need to rebuild.
# It should now be considered a source, not a target.
redo sub  # force rebuild; sub.do now declares dependency on bork
[ "$(cat bork.log)" = "xxx" ] || exit 40
[ "$(cat sub.log)" = "yyyy" ] || exit 41
redo-sources | qgrep '^bork$' || exit 42
redo-targets | qgrep '^bork$' && exit 43

exit 0
