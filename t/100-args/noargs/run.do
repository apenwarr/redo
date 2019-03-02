rm -f all
redo-ifchange  # should not default to 'all' since not running from top level
[ ! -e all ] || exit 11
