./need.sh python kvm busybox

redo-ifchange "$2.initrd" memcalc.py
rm -f "$3.out" "$3.code"

# Linux only allows an initrd of size < 50% of RAM,
# so set a RAM amount based on the initrd size.
mem=$(./memcalc.py "$2.initrd")
echo "$2: kvm memory required: $mem" >&2

kvm \
	-m "$mem" \
	-kernel /boot/vmlinuz-$(uname -r) \
	-initrd "$2.initrd" \
	-append 'rdinit=/rdinit panic=1 console=ttyS0 loglevel=4' \
	-no-reboot \
	-display none \
	-chardev stdio,mux=on,id=char0 \
	-chardev file,id=char1,path="$3.out" \
	-chardev file,id=char2,path="$3.code" \
	-serial chardev:char0 \
	-serial chardev:char1 \
	-serial chardev:char2 >&2
read rv <$3.code || true
[ -z "$rv" ] && exit 99
if [ "$rv" -eq 0 ]; then
	sed -e 's/\r//g' "$3.out" >$3
	echo "ok." >&2
else
	echo "kvm program returned error: $rv" >&2
fi
rm -f "$3.out" "$3.code"
exit "$rv"
