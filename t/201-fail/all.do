rm -f fail
! redo-ifchange fail >&/dev/null || exit 44  # expected to fail
touch fail
../flush-cache
redo-ifchange fail >&/dev/null || exit 55  # expected to pass
