# this shouldn't be allowed; stdout is connected to $3 already, so if we
# replace it *and* write to stdout, we're probably confused.
echo hello world
rm -f $3
echo goodbye world >$3
