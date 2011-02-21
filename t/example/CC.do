redo-ifchange config.sh
. ./config.sh
exec >$3
cat <<-EOF
	redo-ifchange \$1.c
	gcc $CFLAGS -MD -MF \$3.deps -o \$3 -c \$1.c
	read DEPS <\$3.deps
	rm -f \$3.deps
	redo-ifchange \${DEPS#*:}
EOF
chmod +x $3
