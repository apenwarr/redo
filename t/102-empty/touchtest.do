# This may have been leftover from a previous run, when switching
# between "real" redo and minimal/do, so clean it up.
rm -f touch1

# simply create touch1
echo 'echo hello' >touch1.do
redo touch1
[ -e touch1 ] || exit 55
[ "$(cat touch1)" = "hello" ] || exit 56

# ensure that 'redo touch1' always re-runs touch1.do even if we have
# already built touch1 in this session, and even if touch1 already exists.
echo 'echo hello2' >touch1.do
redo touch1
[ "$(cat touch1)" = "hello2" ] || exit 57

# ensure that touch1 is rebuilt even if it got deleted after the last redo
# inside the same session.  Also ensure that we can produce a zero-byte
# output file explicitly.
rm -f touch1
echo 'touch $3' >touch1.do
redo touch1
[ -e touch1 ] || exit 66
[ -z "$(cat touch1)" ] || exit 67

# Also test that zero bytes of output does not create the file at all, as
# opposed to creating a zero-byte file.
rm -f touch1
echo 'touch touch1-ran' >touch1.do
redo touch1
[ -e touch1 ] && exit 75
[ -e touch1-ran ] || exit 76
rm -f touch1-ran

# Make sure that redo-ifchange *won't* rebuild touch1 if we have already
# built it, even if building it did not produce an output file.
redo-ifchange touch1
[ -e touch1 ] && exit 77
[ -e touch1-ran ] && exit 78

rm -f touch1.do
