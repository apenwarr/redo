rm -f $1.start $1.end
echo 'second start' >&2
: >$1.start
redo 2.x
echo 'second sleep' >&2
redo-ifchange first  # wait until 'first' finishes, if it's running
echo 'second end' >&2
: >$1.end
