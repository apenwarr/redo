(
	echo native
	echo fake-always-fails
	if [ -z "$NO_SLOW_TESTS" ]; then
		IFS=:
		for dir in $PATH; do
			for d in "$dir"/*-cc "$dir"/*-gcc; do
				base=${d##*/}
				arch=${base%-*}
				if [ -x "$d" ]; then echo "$arch"; fi
			done
		done
	fi
) >$3
redo-always
redo-stamp <$3
