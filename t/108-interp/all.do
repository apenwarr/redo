rm -f exe1.log exe2.log

redo a b

[ "$(cat exe1.log)" = "test a.do a a .redo/a.out/a" ] || exit 11
[ "$(cat exe2.log)" = "b.do b b .redo/b.out/b" ] || exit 12

