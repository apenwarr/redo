rm -f always1 always1.log

cd ..
redo t/always1
cd t
[ "$(wc -l <always1.log)" -eq 1 ] || exit 11

# This shouldn't rebuild, but because other people might be running
# flush-cache in parallel with us, we can't be 100% sure it won't.  So don't
# test it.
#redo-ifchange always1
#[ "$(wc -l <always1.log)" -eq 1 ] || exit 21

./flush-cache
redo-ifchange always1
. ./skip-if-minimal-do.sh
[ "$(wc -l <always1.log)" -eq 2 ] || exit 31

./flush-cache
redo-ifchange always1
[ "$(wc -l <always1.log)" -eq 3 ] || exit 41

cd ..
./t/flush-cache
redo-ifchange t/always1
[ "$(wc -l <t/always1.log)" -eq 4 ] || exit 51
