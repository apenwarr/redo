fs=${1%.fs}
rm -rf "$fs" "$fs.fakeroot"

redo-ifchange debootstrap.fs
fakeroot -i debootstrap.fakeroot -s "$fs.fakeroot" \
	cp -a debootstrap/. "$fs" >&2

# Work around bug (in fakechroot?) where /lib64 symlink ends up pointing
# at an absolute path including $PWD, rather than inside the chroot.
# Rather than fix the symlink, we'll just make sure $PWD is a link to /,
# so that the "wrong" symlinks correctly resolve.
pwdir=$(dirname "$PWD/bootstrap/")
mkdir -p "$fs/$pwdir/debootstrap"
dots=$(echo "$pwdir/" | sed -e 's,[^/]*/,../,g')
ln -s "${dots}lib" "$fs/$pwdir/debootstrap/lib"

# /init script is what we run in 'docker run'
cat >"$fs/init" <<-EOF
	#!/bin/sh
	dpkg -l | wc -l
EOF
chmod a+x "$fs/init"

redo-ifchange "$fs/bin/sh"
