exec >&2
redo-ifchange \
	file.x.y.z file.z file \
	a/b/file.x.y.z a/b/file.y.z a/b/file.z a/b/file \
	a/d/file.x.y.z a/d/file.y.z a/d/file.z a/d/file

(cd a/b && redo-ifchange ../file.x.y.z ../file.y.z ../file.z ../file)

check()
{
	if [ "$(cat $1)" != "$2" ]; then
		echo "$1 should contain '$2'"
		echo " ...got '$(cat $1)'"
		exit 44
	fi
}

check file.x.y.z "root file.x.y.z ."
check file.z "root file.z ."
check file "root file ."

check a/file.x.y.z "default.x.y.z file .x.y.z"
check a/file.y.z "default.z file.y .z"
check a/file.z "default.z file .z"
check a/file "root a/file a"

check a/b/file.x.y.z "file file.x.y.z"
check a/b/file.y.z "default.y.z file .y.z"
check a/b/file.z "default.z b/file .z"
check a/b/file "root a/b/file a/b"

check a/d/file.x.y.z "default file.x.y.z"
check a/d/file.y.z "default file.y.z"
check a/d/file.z "default file.z"
check a/d/file "default file"

