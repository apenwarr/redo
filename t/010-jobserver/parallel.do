# We should be running in parallel with a jobserver shared with second.do.
# Give second.do some time to start but not finish.
sleep 1

[ -e parallel2.start ] || exit 31
! [ -e parallel2.end ] || exit 32
