PREFIX=/a/b/c/d/e redo vartest2
read x <vartest2
[ "$x" = "/a/b/c/d/e" ] || exit 45
