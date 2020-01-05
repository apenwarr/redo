redo-ifchange arches configure redoconf/utils.sh

config() {
	local dir="$1" arch="$2"
	shift
	shift
	[ -d "$dir" ] || mkdir "$dir"
	(
		cd "$dir" &&
		../configure --host="$arch" "$@" &&
		echo "$dir"
	)
}

dirs=$(
	for d in $(cat arches); do
		if [ "$d" = "native" ]; then
			arch=""
		else
			arch="$d"
		fi
		config "out.$d" "$arch"
		config "out.$d.static" "$arch" "--enable-static"
		config "out.$d.opt" "$arch" "--enable-optimization"
	done
)

for dir in $dirs; do
	echo "$dir/rc/CC.rc"
done | xargs redo-ifchange

for dir in $dirs; do
	( cd "$dir" &&
	  set --;
	  . ./redoconf.rc &&
	  rc_include rc/CC.rc &&
	  [ -n "$HAVE_CC" ] &&
	  echo "$dir"
	) || (echo "Skipping '$dir' - no working C compiler." >&2)
done >$3

wait
