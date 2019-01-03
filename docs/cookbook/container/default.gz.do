redo-ifchange "$2"

# On freebsd, 'gzip --rsyncable' fails but returns 0.
# We have to detect lack of --rsyncable some other way.
gzt=$(gzip --rsyncable -c </dev/null 2>/dev/null | wc -c)
if [ "$gzt" -gt 0 ]; then
	# when available, --rsyncable makes compressed
	# files much more efficient to rsync when they
	# change slightly.
	gzip --rsyncable -c <$2 >$3
else
	gzip -c <$2 >$3
fi
