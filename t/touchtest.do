echo 'echo hello' >touch1.do
redo touch1
[ -e touch1 ] || exit 55
rm -f touch1
echo 'touch $3' >touch1.do
redo touch1
[ -e touch1 ] || exit 66
[ -z "$(cat touch1)" ] || exit 77
rm -f touch1.do
