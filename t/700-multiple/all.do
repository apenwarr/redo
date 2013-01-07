touch dep
mkdir -p x/y
: > x/y/z.dual.log
redo x/y/z.dual

[ -e x/y/z.dual.a ] || exit 11
[ -e x/y/z.dual.b ] || exit 12
[ $(wc -l <x/y/z.dual.log) -eq 1 ] || exit 13

../flush-cache
echo $RANDOM > dep
redo-ifchange x/y/z.dual.a

[ -e x/y/z.dual.a ] || exit 21
[ -e x/y/z.dual.b ] || exit 22
[ $(wc -l <x/y/z.dual.log) -eq 2 ] || exit 23

../flush-cache
redo-ifchange x/y/z.dual

[ -e x/y/z.dual.a ] || exit 31
[ -e x/y/z.dual.b ] || exit 32
[ $(wc -l <x/y/z.dual.log) -eq 2 ] || exit 33
