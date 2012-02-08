. ../skip-if-minimal-do.sh

rm -f pleasefail
redo passfail
[ -e passfail ] || exit 42
PF1=$(cat passfail)
touch pleasefail
redo passfail 2>/dev/null && exit 43
[ -e passfail ] || exit 44
PF2=$(cat passfail)
[ "$PF1" = "$PF2" ] || exit 45
rm -f pleasefail
redo passfail || exit 46
PF3=$(cat passfail)
[ "$PF1" != "$PF3" ] || exit 47
