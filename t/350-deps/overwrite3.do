# we don't delete $3 here, we just truncate and overwrite it.  But redo
# can detect this by checking the current file position of our stdout when
# we exit, and making sure it equals either 0 or the file size.
#
# If it doesn't, then we accidentally wrote to *both* stdout and a separate
# file, and we should get warned about it.
echo hello world
echo goodbye world >$3
