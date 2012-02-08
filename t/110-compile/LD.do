exec >$3
cat <<-EOF
	OUT="\$1"
	shift
	gcc -Wall -o "\$OUT" "\$@"
EOF
chmod a+x $3
