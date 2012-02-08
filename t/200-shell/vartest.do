PREFIX=/a/b/c/d/e redo chicken.vartest
read x <chicken.vartest
[ "$x" = "/a/b/c/d/e" ] || exit 45
