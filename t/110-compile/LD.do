exec >$3
cat <<-EOF
	OUT="\$1"
	shift
	cc -Wall -o "\$OUT" "\$@"
EOF
chmod a+x $3
