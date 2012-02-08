echo 'echo hello' >silence.do
redo silence
[ -e silence ] || exit 55
echo 'true' >silence.do
redo silence
. ../skip-if-minimal-do.sh
[ ! -e silence ] || exit 66
rm -f silence.do
