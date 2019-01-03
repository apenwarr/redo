d=$PWD
redo-ifchange "$2.fs"

if [ -e "$2.diffbase" ]; then
	redo-ifchange "$2.diffbase"
	read diffbase <$2.diffbase
	diffbase=$diffbase.list
	redo-ifchange "$diffbase"
else
	diffbase=/dev/null
	redo-ifcreate "$2.diffbase"
fi

(
	cd "$2" &&
	find . -print | sort | "$d/try_fakeroot.sh" "$d/$2.fakeroot" "$d/fileids.py"
) >$1.tmp

comm -1 -3 "$diffbase" "$1.tmp" >$3
rm -f "$1.tmp"

# Sanity check
nbytes=$(wc -c <"$3")
test $nbytes -gt 0
