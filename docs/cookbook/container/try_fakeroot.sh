#!/bin/sh
frfile=$1
shift
broken=
fakeroot true 2>/dev/null || broken=1
if [ -z "$broken" ] && [ -e "$frfile" ]; then
	redo-ifchange "$frfile"
	exec fakeroot -i "$frfile" "$@"
elif [ -z "$broken" ]; then
	exec fakeroot "$@"
else
	exec "$@"
fi
