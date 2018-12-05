redo-ifchange whichpython
read py <whichpython
cat >$3 <<-EOF
	#!/bin/sh
	exec $py "\$@"
EOF
chmod a+x $3
