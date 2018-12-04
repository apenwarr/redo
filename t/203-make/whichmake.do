if type gmake >/dev/null 2>/dev/null; then
	make=gmake
elif type make >/dev/null 2>/dev/null; then
	make=make
else
	# No make installed?  That's okay, this test
	# isn't *that* important.
	make=:
fi

cat >$3 <<-EOF
	#!/bin/sh
	$make "\$@"
EOF
chmod a+x $3

