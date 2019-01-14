# We can pull in the 'hello' binary built in an earlier
# example.  Notice that it's safe to have dependencies
# that cross directory boundaries, even when we're building
# both of those directories in parallel.
FILES="
	/bin/sh
	../hello/hello
"
if [ -x /bin/busybox ]; then
	# Optional, except for runkvm
	FILES="$FILES /bin/busybox"
else
	redo-ifcreate /bin/busybox
fi
redo-ifchange $FILES

fs=${1%.fs}
rm -rf "$fs"
mkdir -p "$fs/bin"
cp $FILES "$fs/bin/"
ln -s bin/hello "$fs/init"

redo-ifchange "$fs/bin/sh"
