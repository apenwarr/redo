rm -rf x do/log
mkdir -p x/y
redo x/y/z

[ -e x/y/z ] || exit 11
[ $(wc -l <do/log) -eq 1 ] || exit 12

