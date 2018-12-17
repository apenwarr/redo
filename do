#!/bin/sh
#
# Bootstrap script, so we can build and test redo using (mostly) redo.
# Before redo is available, we have to use minimal/do to build it.  After
# that, we switch to real redo.
#
# NOTE: Don't use this as a model for your own redo projects!  It's friendly
# to provide a 'do' script at the top of your project for people who haven't
# installed redo, but that script is usually just a copy of minimal/do,
# because your project probably doesn't have the same bootstrap problem that
# redo itself does.
#

die() {
	echo "$0:" "$@" >&2
	exit 42
}

usage() {
	echo "Usage: $0 [redo-args...] <target>" >&2
	echo "   where valid targets are: build all test install clean" >&2
	echo "   and redo-args are optional args for redo, like -j10, -x" >&2
	exit 10
}

mydir=$(dirname "$0")
cd "$(/bin/pwd)" && cd "$mydir" || die "can't find self in dir: $mydir"

args=
while [ "$1" != "${1#-}" ]; do
	args="$args $1"
	shift
done

if [ "$#" -gt 1 ]; then
	usage
fi

if [ -n "$args" -a "$#" -lt 1 ]; then
	usage
fi

if [ "$#" -lt 1 ]; then
	# if no extra args given, use a default target
	target=all
else
	target=$1
fi


build() {
	./minimal/do -c bin/all || die "failed to compile redo."
	bin/redo bin/all || die "redo failed self test."
}

clean() {
	./minimal/do -c clean || die "failed to clean."
	rm -rf .redo .do_built .do_built.dir
}

case $target in
	build)
		build
		;;
	all|install)
		build && bin/redo $args "$target"
		;;
	test)
		# Be intentionally confusing about paths, to try to
		# detect bugs.
		rm -f 't/symlink path'
		ln -s .. 't/symlink path' || die 'failed to make test dir.'
		cd 't/symlink path/t/symlink path'
		# First test minimal/do
		build
		# Add ./redo to PATH so we launch with redo/sh as the shell
		PATH=$PWD/redo:$PATH minimal/do test || die "minimal/do test failed"
		clean
		build
		# Now switch to testing 'real' redo
		bin/redo $args test || die "redo test failed"
		;;
	clean)
		clean
		;;
	*)
		echo "$0: unknown target '$target'" >&2
		exit 11
		;;
esac
