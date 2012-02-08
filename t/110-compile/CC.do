exec >$3
cat <<-EOF
	gcc -Wall -o /dev/fd/1 -c "\$1"
EOF
chmod a+x $3
