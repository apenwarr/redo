# Run from the source dir.
#
# We'll make sure the out/ dir exists and that
# a C++ compiler is available, then redo out/all,
# which is implemented in the file all.od.
#
# Note that a "normal" project might not have an all.do
# at all; the end user would be expected to make an
# output dir, run ../configure, and then redo from there.
# But we want this file to build as part of the redo
# examples, so there needs to be a toplevel all.do in
# each example.
#
. ./skip-if-no-cxx.sh
redo-ifchange out/all
