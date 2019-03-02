rm -f x/shouldfail

log=$PWD/$1.log

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

# These should all fail because there is no matching .do file.
# In previous versions of redo, it would accidentally try to use
# $PWD/default.do even for ../path/file, which is incorrect.  That
# could cause it to return success accidentally.

rm -f "$log"
cd inner
expect_fail 11 redo ../x/shouldfail
expect_fail 12 redo-ifchange ../x/shouldfail

rm -f "$log"
cd ../inner2
expect_fail 21 redo ../x/shouldfail2
expect_fail 22 redo-ifchange ../x/shouldfail2

exit 0
