# Test that -j1 really serializes all sub-redo processes.
rm -f *.sub *.spin *.x first second *.start *.end
redo first second
