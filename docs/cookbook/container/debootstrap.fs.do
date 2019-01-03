exec >&2
fs=${1%.fs}
rm -rf "$fs" "$fs.fakeroot"

redo-ifchange debdownload.fs debootstrap.options
cp -a debdownload/. "$fs"
eatmydata \
	fakechroot \
	fakeroot -s "$fs.fakeroot" \
	debootstrap $(cat debootstrap.options) "$fs"

# Clean up installed package files
rm -f "$fs"/var/cache/apt/archives/*.deb \
	"$fs"/var/cache/apt/*.bin \
	"$fs"/var/lib/apt/lists/*Packages \
	"$fs"/var/lib/apt/lists/*Sources \
	"$fs"/var/lib/apt/lists/debootstrap*

redo-ifchange "$fs/bin/sh"
