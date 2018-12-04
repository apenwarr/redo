exec >&2

redo-always
(
	cd ../redo
	for d in cmd_*.py; do
		d=${d#cmd_}
		d=${d%.py}
		if [ "$d" = "redo" ]; then
			echo redo
		else
			echo "redo-${d%.py}"
		fi
	done
) >$3
redo-stamp <$3
