# minimal/do doesn't need to "support" cyclic dependencies, because
# they're always a bug in the .do scripts :)
. ../skip-if-minimal-do.sh

! redo a >/dev/null 2>&1 || exit 204
