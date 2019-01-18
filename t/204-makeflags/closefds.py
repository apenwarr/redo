import subprocess, sys, os

# subprocess.call(close_fds=True) is unfortunately not a good idea,
# because some versions (Debian's python version?) try to close inordinately
# many file descriptors, like 0..1000000, which takes a very long time.
#
# We happen to know that redo doesn't need such huge fd values, so we'll
# just cheat and use a smaller range.
os.closerange(3, 1024)
rv = subprocess.call(sys.argv[1:])
sys.exit(rv)

