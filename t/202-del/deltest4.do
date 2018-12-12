rm -rf x
redo x/a.spam2
[ "$(cat x/a.spam2)" = "redir" ] || exit 11
redo x/a.spam2
[ "$(cat x/a.spam2)" = "redir" ] || exit 12
redo x/b.spam2
[ "$(cat x/b.spam2)" = "redir" ] || exit 13

rm -rf x
redo x/a.spam1
[ "$(cat x/a.spam1)" = "stdout" ] || exit 21
redo x/a.spam1
[ "$(cat x/a.spam1)" = "stdout" ] || exit 22
redo x/b.spam1
[ "$(cat x/b.spam1)" = "stdout" ] || exit 23
