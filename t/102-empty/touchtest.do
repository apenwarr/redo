# This may have been leftover from a previous run, when switching
# between "real" redo and minimal/do, so clean it up.
rm -f touch1

echo 'echo hello' >touch1.do
redo touch1
[ -e touch1 ] || exit 55
rm -f touch1
echo 'touch $3' >touch1.do
redo touch1
[ -e touch1 ] || exit 66
[ -z "$(cat touch1)" ] || exit 77
rm -f touch1.do
