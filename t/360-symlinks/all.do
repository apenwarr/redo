rm -f a a.extra b b.did
d0=""
redo a
redo-ifchange b
d1=$(cat b.did)
[ "$d0" != "$d1" ] || exit 11

# b only rebuilds if a changes
../flush-cache
redo-ifchange b
d2=$(cat b.did)
[ "$d1" = "$d2" ] || exit 12

# forcibly changing a should rebuild b.
# a is already symlink to a.extra, but redo shouldn't care about the
# target of symlinks, so it shouldn't freak out that a.extra has changed.
# Anyway, b should still rebuild because a was rebuilt.
../flush-cache
redo a
redo-ifchange b
d3=$(cat b.did)
[ "$d2" != "$d3" ] || exit 13

# Explicitly check that changing a's symlink target (a.extra) does *not*
# trigger a rebuild of b, because b depends on the stamp of the symlink,
# not what the symlink points to.  In redo, you declare dependencies on
# specific filenames, not the things they happen to refer to.
../flush-cache
touch a.extra
redo-ifchange b
d4=$(cat b.did)
[ "$d3" = "$d4" ] || exit 14
