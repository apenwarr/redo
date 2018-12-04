# Make sure everything has been built before we start
redo-ifchange all

# Ensure that the hello program, when run, says
# hello like we expect.
if ./hello | grep -i 'hello' >/dev/null; then
    echo "success" >&2
    exit 0
else
    echo "missing 'hello' message!" >&2
    exit 1
fi
