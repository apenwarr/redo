exec >&2
rm -f x pid
pid=$$
echo "$pid" >pid
xout=$(redo x)

[ "$(printf "$xout" | wc -l)" -eq 0 ] || exit 2

if [ -n "$REDO_LOG" ]; then
	# redo has redo-log support enabled, so check that it saves logs.

	# recursive log dump should show both x and y stderr.
	redo-log -ru x | grep -q "^$pid x stderr" || exit 10
	redo-log -ru x | grep -q "^$pid y stderr" || exit 11

	# stdout captured by redo into the files x and y, *not* to log
	redo-log -ru x | grep -q "^$pid x stdout" && exit 20
	redo-log -ru x | grep -q "^$pid y stdout" && exit 21
	[ "$(cat x)" = "$pid x stdout" ] || exit 22
	[ "$(cat y)" = "$pid y stdout" ] || exit 23

	# non-recursive log dump of x should *not* include y
	redo-log x | grep -q "^$pid y stdout" && exit 30
	redo-log x | grep -q "^$pid y stderr" && exit 31

	redo a/b/xlog
	(cd a && redo b/xlog)

        # Test retrieval from a different $PWD.
        (
            cd a/b || exit 40
            redo-log -ru ../../x | grep -q "^$pid x stderr" || exit 41
            redo-log -ru ../../x | grep -q "^$pid y stderr" || exit 42
        ) || exit
fi

# whether or not redo-log is available, redirecting stderr should work.
pid=$$-bork
rm -f x pid
echo "$pid" >pid
out=$(redo x 2>&1)

# x's stderr should obviously go where we sent it
echo "$out" | grep -q "^$pid x stderr" || exit 50

# This one is actually tricky: with redo-log, x's call to 'redo y' would
# normally implicitly redirect y's stderr to a new log.  redo needs to
# detect that we've already redirected it where we want, and not take it
# away.
echo "$out" | grep -q "^$pid y stderr" || exit 51

exit 0
