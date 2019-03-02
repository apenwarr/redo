cat >$3 <<-EOF
	const char *stamp_time(void) {
	    return "$(date +%Y-%m-%d)";
	}
EOF
redo-always
redo-stamp <$3
