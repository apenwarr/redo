exec >&2

case $1 in
	redo-sh)
		redo-ifchange ../redo/sh
		cat >$3 <<-EOF
			#!/bin/sh
			d=\$(dirname "\$0")/..
			[ -x \$d/lib/redo/sh ] && exec \$d/lib/redo/sh "\$@"
			[ -x \$d/redo/sh ] && exec \$d/redo/sh "\$@"
			echo "\$0: fatal: can't find \$d/lib/redo/sh or \$d/redo/sh" >&2
			exit 98
		EOF
		chmod a+x "$3"
		;;
	redo|redo-*)
		redo-ifchange ../redo/whichpython
		read py <../redo/whichpython
		cmd=${1#redo-}
		cat >$3 <<-EOF
			#!$py -S
			import sys, os;
			exe = os.path.realpath(os.path.abspath(sys.argv[0]))
			exedir = os.path.dirname(exe)
			sys.path.insert(0, os.path.join(exedir, '../lib'))
			sys.path.insert(0, os.path.join(exedir, '..'))
			import redo.cmd_$cmd
			redo.cmd_$cmd.main()
		EOF
		chmod a+x "$3"
		;;
	*) echo "$0: don't know how to build '$1'" >&2; exit 99 ;;
esac
