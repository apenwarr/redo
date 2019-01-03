redo-ifchange "$2.fs"

./need.sh unshare

set +e
unshare -r chroot "$2" /init >$3
rv=$?
if [ "$rv" != 0 ]; then
	f=/proc/sys/kernel/unprivileged_userns_clone
	if [ -e "$f" ]; then
		read v <$f
		if [ "$v" -eq 0 ]; then
			echo "Try: echo 1 >$f" >&2
		fi
	fi

	f=/proc/sys/kernel/userns_restrict
	if [ -e "$f" ]; then
		read v <$f
		if [ "$v" -ne 0 ]; then
			echo "Try: echo 0 >$f" >&2
		fi
	fi
fi
exit "$rv"
