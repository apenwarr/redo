# We put the -j options at this toplevel to detect an earlier bug
# where the sub-jobserver wasn't inherited by sub-sub-processes, which
# accidentally reverted to the parent jobserver instead.

redo -j1 serialtest

# Capture log output to parallel.log to hide the (intentional since we're
# testing it) scary warning from redo about overriding the jobserver.
echo 'parallel test...' >&2
if ! redo -j10 paralleltest 2>parallel.log; then
	cat parallel.log >&2
	exit 99
fi
