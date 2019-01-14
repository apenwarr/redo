fs=${1%.fs}

# let's *not* delete this directory; it's okay if previously-downloaded
# excess packages hang around in case we need them later.
#rm -rf "$fs"
mkdir -p "$fs"
redo-ifchange debootstrap.options
debootstrap \
	--download-only \
	--keep-debootstrap-dir \
	$(cat debootstrap.options) \
	"$fs" >&2
redo-ifchange "$fs/debootstrap/debootstrap.log"
