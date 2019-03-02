# This file changes when the list of source files changes.
# If you depend on it, you can make a target that gets
# rebuilt only when it might need to reconsider the
# list of available source files.
find . -name '*.[ch]' -o \
	-name '*.cc' -o \
	-name '*.od' -o \
	-name '*.list' |
grep -v '^\./out\.' |
sort >$3
redo-always
redo-stamp <$3
