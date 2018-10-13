# tests that "set -e" works (.do scripts always run with -e set by default)
rm -f 000-set-minus-e/log
redo 000-set-minus-e/all
if [ "$(cat 000-set-minus-e/log)" != "ok" ]; then
    echo "FATAL! .do file not run with 'set -e' in effect!" >&2
    exit 5
fi

# builds 1xx*/all to test for basic/dangerous functionality.
# We don't want to run more advanced tests if the basics don't work.
/bin/ls 1[0-9][0-9]*/all.do |
sed 's/\.do$//' |
xargs redo
110-compile/hello >&2

# builds most of the rest in parallel
/bin/ls [2-9][0-9][0-9]*/all.do |
sed 's/\.do$//' |
xargs redo

# builds the tests that require non-parallel execution.
# If tests are written carefully, this should only be things that
# are checking for unnecessary extra rebuilds of some targets, which
# might happen after flush-cache.
# FIXME: a better solution might be to make flush-cache less destructive!
/bin/ls [s][0-9][0-9]*/all.do |
sed 's/\.do$//' | {
    while read d; do
        redo "$d"
    done
}
