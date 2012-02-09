# Note: this test expects to be run with 'redo --old-args' or it will fail.
. ../skip-if-minimal-do.sh
[ "$1" = "test" ]
[ "$2" = ".oldargs" ]
[ "$3" != "test.oldargs" ]
