exec >&2   # any output we produce is a log message
no_simple=
no_debian=
no_runlocal=
no_runkvm=
no_docker=

if ! ./need.sh ldd; then
	echo "skipping simple image."
	no_simple=1
fi
if ! ./need.sh debootstrap eatmydata; then
	echo "skipping debian image."
	no_debian=1
fi
if ! ./need.sh fakeroot fakechroot ||
   ! ./try_fakeroot.sh "x" true 2>/dev/null; then
	echo "skipping chroot test."
	no_runlocal=1
	echo "skipping debian image."
	no_debian=1
fi
if ! ./need.sh unshare ||
   ! unshare -r true 2>/dev/null; then
	echo " -- 'unshare -r' command doesn't work."
	echo "skipping chroot test."
	no_runlocal=1
fi
if ! ./need.sh busybox kvm; then
	echo "skipping kvm test."
	no_runkvm=1
fi
if ! ./need.sh docker ||
   ! docker images >/dev/null; then
	echo "skipping docker test."
	no_docker=1
fi
if [ -n "$NO_SLOW_TESTS" ]; then
	echo " -- NO_SLOW_TESTS is set."
	echo "skipping debian image."
	no_debian=1
fi

add() { targets="$targets $*"; }

[ -z "$no_simple" ] && add simple.image.gz
[ -z "$no_simple$no_runlocal" ] && add libs.runlocal
[ -z "$no_simple$no_runkvm" ] && add libs.runkvm
[ -z "$no_simple$no_docker" ] && add simple.rundocker

[ -z "$no_debian" ] && add debian.image
[ -z "$no_debian$no_runlocal" ] && add debian.runlocal
[ -z "$no_debian$no_runkvm" ] && add debian.runkvm
[ -z "$no_debian$no_docker" ] && add debian.rundocker

redo-ifchange $targets

check() {
	label=$1
	shift
	printf "checking %-18s %-35s " "$label:" "$*" >&2
	if test "$@"; then
		printf "ok\n" >&2
	else
		printf "failed\n" >&2
	fi
}

hellocheck() {
	check "$1" "$(cat "$1")" = "Hello, world!"
}

debcheck() {
	check "$1" "$(cat "$1")" -ge "70"
	check "$1" "$(cat "$1")" -le "100"
}

if [ -z "$no_simple" ]; then
	[ -n "$no_runlocal" ] || hellocheck libs.runlocal
	[ -n "$no_runkvm" ] || hellocheck libs.runkvm
	[ -n "$no_docker" ] || hellocheck simple.rundocker
fi

if [ -z "$no_debian" ]; then
	[ -n "$no_runlocal" ] || debcheck debian.runlocal
	[ -n "$no_runkvm" ] || debcheck debian.runkvm
	[ -n "$no_docker" ] || debcheck debian.rundocker
fi
