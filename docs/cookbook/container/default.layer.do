d=$PWD
redo-ifchange "$2.fs" "$2.list"

sed -e 's/ [^ ]*$//' <$2.list |
(
	cd "$2"
	"$d/try_fakeroot.sh" "$d/$2.fakeroot" \
		cpio -Hustar -o
) >$3
