# Test that -j2 really gives us parallel builds with their own tokens.
# (It's hard to test for sure that we have our own tokens, but if we're
# sharing with other tests, we can't be sure that parallel2 will run while
# parallel is running, and the race condition will make this test at least
# be flakey instead of pass, which means there's a bug.)
rm -f *.sub *.spin *.x parallel *.start *.end
redo parallel parallel2
