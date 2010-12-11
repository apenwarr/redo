redo-ifchange config.sh
. ./config.sh
exec >$3
cat <<-EOF
	redo-ifchange \$1.c
	gcc -MD -MF \$3.deps.tmp -o \$3 -c \$1.c
	DEPS=\$(sed -e "s/^\$3://" -e 's/\\\\//g' <\$3.deps.tmp)
	rm -f \$3.deps.tmp
	redo-ifchange \$DEPS
EOF
chmod +x $3
