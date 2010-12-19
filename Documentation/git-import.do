exec >&2
if git show-ref refs/heads/man >/dev/null; then
	(cd .. && git archive man) | tar -xvf -
else
	(cd .. && git archive origin/man) | tar -xvf -
fi


