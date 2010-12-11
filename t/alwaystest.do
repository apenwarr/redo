rm -f always1 always1.log

redo always1
[ "$(wc -l <always1.log)" -eq 1 ] || exit 11

# This shouldn't rebuild, but because other people might be running flush-cache.sh
# in parallel with us, we can't be 100% sure it won't.  So don't test it.
#redo-ifchange always1
#[ "$(wc -l <always1.log)" -eq 1 ] || exit 21

./flush-cache.sh
redo-ifchange always1
[ "$(wc -l <always1.log)" -eq 2 ] || exit 31
