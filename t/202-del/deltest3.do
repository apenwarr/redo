rm -rf destruct
mkdir destruct
cd destruct
cat >destruct1.do <<-EOF
	rm -f *.tmp
	echo 'redir' >\$3
EOF
cat >destruct2.do <<-EOF
	rm -f *.tmp
	echo 'stdout'
EOF

# deleting unused stdout file is a warning at most
redo destruct1 2>destruct1.log || exit 11
[ "$(cat destruct1)" = "redir" ] || exit 12

# deleting *used* stdout file may be a fatal mistake,
# but we won't enforce that, since some redo variants
# might be more accepting or use different tmp file
# algorithms.  So either the file should be correct,
# or it should be missing.
redo destruct2 2>destruct2.log || :
if [ -e "destruct2" ]; then
	[ "$(cat destruct2)" = "stdout" ] || exit 22
fi
