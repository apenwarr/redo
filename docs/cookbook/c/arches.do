IFS=:
echo native >$3
if [ -z "$NO_SLOW_TESTS" ]; then
	for dir in $PATH; do
		for d in "$dir"/*-cc "$dir"/*-gcc; do
			base=${d##*/}
			arch=${base%-*}
			if [ -x "$d" ]; then echo "$arch"; fi
		done
	done >>$3
fi

redo-always
redo-stamp <$3
