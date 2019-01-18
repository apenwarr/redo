# Make sure we can survive if a process closes all file descriptors,
# including any jobserver file descriptors, as long as they also
# unset MAKEFLAGS.
redo-ifchange ../../redo/py

# If we leave MAKEFLAGS set, then it's fair game to complain that the
# advertised file descriptors are gone, because GNU make also complains.
# (Although they only warn while we abort.  They can't abort so that
# they don't break backward compat, but we have no such constraint, because
# redo has always failed for that case.)
#
# On the other hand, we shouldn't have to unset REDO_CHEATFDS, both for
# backward compatibility, and because REDO_CHEATFDS is undocumented.
# redo should recover silently from that problem.
unset MAKEFLAGS
../../redo/py ./closefds.py redo noflags
