[ -e rodir ] && chmod u+w rodir
[ -e rodir/rwdir ] && chmod u+w rodir/rwdir
rm -rf rodir
mkdir rodir rodir/rwdir

cd rodir
cat >default.ro1.do <<-EOF
	chmod u+w "\$(dirname "\$1")"
	echo 'redir' >\$3
EOF
cat >default.ro2.do <<-EOF
	chmod u+w "\$(dirname "\$1")"
	echo 'stdout'
EOF

# Check that:
#  - redo works when the .do file is in a read-only directory.
#  - redo works when the target is in a read-only directory that becomes
#    writable only *after* launching the .do script. (For example, the .do
#    might mount a new read-write filesystem in an otherwise read-only
#    tree.)
chmod a-w . rwdir
redo rwdir/a.ro1
chmod a-w . rwdir
redo rwdir/a.ro2
