exec >&2
for py in intentionally-missing python python3 python2 python2.7; do
	echo "Trying: $py"
	cmd=$(command -v "$py" || true)
	out=$($cmd -c 'print("success")' 2>/dev/null) || true
	if [ "$out" = "success" ]; then
		echo $cmd >$3
		exit 0
	fi
done
exit 10
