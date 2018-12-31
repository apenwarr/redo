# in case we're (erroneously) running in parallel, give second.do some
# time to start but not finish.
echo 'first sleep' >&2
sleep 1

# Because of --shuffle, we can't be sure if first or second ran first, but
# because all.do uses -j1, we *should* expect that if second ran first, it
# at least ran to completion before we ran at all.
if [ -e second.start ]; then
	echo 'first: second already started before we did...' >&2
	[ -e second.end ] || exit 21
	echo 'first: ...and it finished as it should.' >&2
	# no sense continuing the test; can't test anything if second already
	# ran.
	exit 0
fi
echo 'first: second has not started yet, good.' >&2

echo 'first spin' >&2
redo 1.a.spin
[ -e 1.a.spin ] || exit 11
echo 'first spin complete' >&2

! [ -e second.start ] || exit 22
