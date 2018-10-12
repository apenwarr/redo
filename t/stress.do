rm -f $1.log
exec >$1.log

# This test twiddles the same files over and over, and seems to trigger race conditions
# in redo if run repeatedly with a large redo -j.
for d in $(seq 25); do
    echo "stress test: cycle $d" >&2
    ./flush-cache 2>&1
    redo 950-curse/all 2>&1 || { rv=$?; echo "stress test: log is $1.log" >&2; exit $rv; }
done
