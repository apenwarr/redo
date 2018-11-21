rm -f a a.ran a.final b b.ran *.[123] dir/*.[123]
mkdir -p dir

reads() {
	aold=$aval
	bold=$bval
	read aval <a.ran || :
	read bval <b.ran || :
}

# Basic setup should build a and b
aval=
bval=
redo a
redo-ifchange b
reads
[ "$aold" != "$aval" ] || exit  11
[ "$bold" != "$bval" ] || exit 111

# b only rebuilds if a changes
../flush-cache
redo-ifchange b
reads
[ "$aold" = "$aval" ] || exit  12
[ "$bold" = "$bval" ] || exit 112

. ../skip-if-minimal-do.sh

# forcibly building a should trigger rebuild of b, which depends on it.
# Previous versions of redo would be upset that a.final had changed.
../flush-cache
redo a
redo-ifchange b
reads
[ "$aold" != "$aval" ] || exit  13
[ "$bold" != "$bval" ] || exit 113

# a.final is the target of the a symlink.  We should notice when it changes,
# even if a was not rebuilt.  Although it does get rebuilt, because a's
# stamp is now different from the database.
echo xx >>a.final
../flush-cache
redo-ifchange b
reads
[ "$aold" != "$aval" ] || exit  14
[ "$bold" != "$bval" ] || exit 114

# We should also notice if a.final is removed.
# Now a is a "dangling" symlink.
rm -f a.final
../flush-cache
redo-ifchange b
reads
[ "$aold" != "$aval" ] || exit  15
[ "$bold" != "$bval" ] || exit 115

# If the symlink becomes no-longer-dangling, that should be dirty too.
echo "splash" >a.final
../flush-cache
redo-ifchange b
reads
[ "$aold" != "$aval" ] || exit  16
[ "$bold" != "$bval" ] || exit 116

# We ought to know the difference between a, the symlink, and its target.
# If a is replaced with a.final directly, that's a change.
rm -f a
mv a.final a
../flush-cache
redo-ifchange b >/dev/null 2>&1  # hide "you changed it" message
reads
[ "$aold"  = "$aval" ] || exit  17  # manual override prevented rebuild
[ "$bold" != "$bval" ] || exit 117
