exec >&2
rm -f a b *.log stamp

echo 1 >stamp
redo b
[ "$(cat b)" = "hello-a-1-b" ] || exit 11

../../flush-cache
echo 2 >stamp
redo-ifchange b
[ "$(cat b)" = "hello-a-1-b" ] || exit 21  # a unchanged; b not redone

. ../../skip-if-minimal-do.sh

# Unfortunately the test below depends on the specific wording of the
# "override" warning message, of the form:
#    redo: a - you modified it; skipping
# That's because this is specifically a test that the warning message
# gets generated.  I added that test because (of course) when we didn't
# test it, the warning message accidentally got broken.  Oops.  If you
# rephrase the message, you'll have to also change the test.

../../flush-cache
echo 3 >stamp
echo over-a >a
redo-ifchange b >$1.log 2>&1
[ "$(cat b)" = "over-a-3-b" ] || exit 31  # a overwritten, b redone
grep "a - " "$1.log" >/dev/null || exit 32  # expected a warning msg

../../flush-cache
echo 4 >stamp
redo-ifchange b >$1.log 2>&1
[ "$(cat b)" = "over-a-3-b" ] || exit 41  # a not changed, b not redone
grep "a - " "$1.log" >/dev/null || exit 42  # still expect a warning msg
