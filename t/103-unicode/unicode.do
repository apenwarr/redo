# Test that redo can handle a script whose path contains non-ASCII characters.
# Note: the test directory is intentionally *not* a normalized unicode
# string, ie. filesystems like macOS will convert it to a different string
# at creation time. This tests weird normalization edge cases.
#
# Unfortunately, on macOS with APFS, it may helpfully normalize the path at
# *create* time, but not on future *open* attempts. Thus, we let the shell
# figure out what directory name actually got created, then pass that to redo.
# Hence the weird wildcard expansion loop.
rm -rf test-uni*.tmp
mkdir "test-uniçøðë.tmp"
for p in test-uni*.tmp; do
	: >$p/test1.do
	redo "$p/test1"
done

