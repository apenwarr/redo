# This may have been leftover from a previous run, when switching
# between "real" redo and minimal/do, so clean it up.
rm -f silence

echo 'echo hello' >silence.do
redo silence
[ -e silence ] || exit 55
echo 'true' >silence.do
redo silence
. ../skip-if-minimal-do.sh
[ ! -e silence ] || exit 66
rm -f silence.do
