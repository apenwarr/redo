rm -f x/shouldfail

log=$PWD/$1.log
rm -f "$log"

expect_fail() {
	local rv=$1
	shift
	if ("$@") >>$log 2>&1; then
		cat "$log" >&2
		echo "unexpected success:" "$@" >&2
		return $rv
	else
		return 0
	fi
}

cd inner
expect_fail 11 redo ../x/shouldfail   # should fail
expect_fail 12 redo-ifchange ../x/shouldfail  # should fail again

exit 0
