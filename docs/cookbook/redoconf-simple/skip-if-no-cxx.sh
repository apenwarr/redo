# Make sure there is an out/ directory and
# the configure script was run.
redo-ifchange configured

# Abort if we can't find a C++ compiler for
# this platform.
if ! (cd out &&
      . ./redoconf.rc &&
      rc_include rc/CXX.rc &&
      [ -n "$HAVE_CXX" ]); then
	echo "$1: No C++ compiler: skipping." >&2
	exit 0
fi

