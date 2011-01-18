redo-ifchange ../version/vars $1.md
. ../version/vars
sed -e "s/%VERSION%/$TAG/" -e "s/%DATE%/$DATE/" $1.md
