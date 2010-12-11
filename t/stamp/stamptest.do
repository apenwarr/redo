rm -f stampy usestamp usestamp2 stampy.log usestamp.log usestamp2.log
echo one >inp

../flush-cache.sh
redo stampy
[ "$(wc -l <stampy.log)" -eq 1 ] || exit 11

# stampy already exists, so we won't generate it a second time, even though
# usestamp depends on it.
../flush-cache.sh
redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 1 ] || exit 21
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 12

../flush-cache.sh
redo stampy
[ "$(wc -l <stampy.log)" -eq 2 ] || exit 31
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 32

# same as above: stampy is already up-to-date, so it won't be redone.
../flush-cache.sh
redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 2 ] || exit 41
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 42

# stampy depends on bob, so we'll have to rebuild stampy automatically.  But
# stampy's checksum will still be identical.
../flush-cache.sh
redo bob
redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 3 ] || exit 43
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 44

# Make sure the previous step correctly marked stampy and usestamp as up-to-date
# even though *neither* of them is newer than bob.
../flush-cache.sh
redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 3 ] || exit 45
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 46

# now we're changing the contents of stampy.
../flush-cache.sh
echo two >inp
redo stampy
[ "$(wc -l <stampy.log)" -eq 4 ] || exit 51
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 52

redo-ifchange usestamp usestamp2
[ "$(wc -l <stampy.log)" -eq 4 ] || exit 61
[ "$(wc -l <usestamp.log)" -eq 2 ] || exit 62
[ "$(wc -l <usestamp2.log)" -eq 1 ] || exit 62

# when we delete the file and it gets regenerated identically, it's as good as
# never having been deleted.  So usestamp won't need to change.
../flush-cache.sh
rm -f stampy
redo-ifchange usestamp usestamp2
[ "$(wc -l <stampy.log)" -eq 5 ] || exit 71
[ "$(wc -l <usestamp.log)" -eq 2 ] || exit 72
[ "$(wc -l <usestamp2.log)" -eq 1 ] || exit 73

# this simple test used to cause a deadlock.
../flush-cache.sh
rm -f stampy
redo-ifchange stampy
[ "$(wc -l <stampy.log)" -eq 6 ] || exit 74
