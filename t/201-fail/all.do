rm -f this-doesnt-exist
! redo this-doesnt-exist >&/dev/null || exit 32  # expected to fail
! redo-ifchange this-doesnt-exist >&/dev/null || exit 33  # expected to fail
redo-ifcreate this-doesnt-exist >&/dev/null || exit 34  # expected to pass



rm -f fail
! redo-ifchange fail >&/dev/null || exit 44  # expected to fail

touch fail
../flush-cache
# since we created this file by hand, fail.do won't run, so it won't fail.
redo-ifchange fail >&/dev/null || exit 55  # expected to pass
