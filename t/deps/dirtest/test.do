touch t?.do
for first in t1 t2 t3; do
	for second in t1 t2 t3; do
		rm -f log dir1/log dir1/stinky
		. ../../flush-cache.sh
		redo $first
		touch $second.do
		. ../../flush-cache.sh
		redo $second
		. ../../flush-cache.sh
		redo-ifchange $second
		C1="$(wc -l <dir1/log)"
		C2="$(wc -l <log)"
		if [ "$C1" != 1 -o "$C2" != 2 ]; then
			echo "failed: $first>$second, c1=$C1, c2=$C2" >&2
			exit 55
		fi
	done
done
