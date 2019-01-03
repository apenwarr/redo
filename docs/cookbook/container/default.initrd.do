redo-ifchange "$2.fs" rdinit
d=$PWD
fs=$2
(
	(cd "$fs" && find . -print0 |
	 "$d/try_fakeroot.sh" "$d/$2.fakeroot" \
	 	cpio -Hnewc -0 -o)
	printf 'rdinit\0' | cpio -Hnewc -0 -o
) >$3
