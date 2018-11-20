read pid <pid
echo "$pid x stdout"
echo "$pid x stderr" >&2
rm -f y
redo y
