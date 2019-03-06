# Ensure that an out/ directory exists and that
# it has been configured (ie. ../configure has been run).
[ -d out ] || (mkdir out && cd out && ../configure)

# By declaring a dependency on this file *after* running
# configure, we can tell redo that reconfiguration is
# needed if this file ever disappears (for example, if
# the whole out/ directory disappears).
redo-ifchange out/default.do
