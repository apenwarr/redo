redo-ifchange arches configure redoconf/utils.sh

config() {
	local dir="$1" arch="$2"
	shift
	shift
	[ -d "$dir" ] || mkdir "$dir"
	(
		cd "$dir" &&
		../configure --host="$arch" "$@" &&
		( set --;
		  . ./redoconf.rc &&
		  rc_include rc/CC.rc &&
		  [ -n "$HAVE_CC" ]
		) &&
		echo "$dir"
	) || (echo "Skipping arch '$arch' $*" >&2)
}

for d in $(cat arches); do
	if [ "$d" = "native" ]; then
		arch=""
	else
		arch="$d"
	fi
	config "out.$d" "$arch" &
	config "out.$d.static" "$arch" "--enable-static" &
	config "out.$d.opt" "$arch" "--enable-optimization" &
done >$3

wait
