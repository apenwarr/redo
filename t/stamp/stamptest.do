rm -f stampy usestamp stampy.log usestamp.log
echo one >inp

../flush-cache.sh
redo stampy
[ "$(wc -l <stampy.log)" -eq 1 ] || exit 11

redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 1 ] || exit 21
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 12

../flush-cache.sh
redo stampy
[ "$(wc -l <stampy.log)" -eq 2 ] || exit 31
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 32

redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 2 ] || exit 41
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 42

../flush-cache.sh
echo two >inp
redo stampy
[ "$(wc -l <stampy.log)" -eq 3 ] || exit 51
[ "$(wc -l <usestamp.log)" -eq 1 ] || exit 52

redo-ifchange usestamp
[ "$(wc -l <stampy.log)" -eq 3 ] || exit 61
[ "$(wc -l <usestamp.log)" -eq 2 ] || exit 62
