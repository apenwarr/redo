vars=$(
	env | {
		IFS="="
		while read key value; do
			if [ "$key" != "${key#REDO}" ] ||
			   [ "$key" != "${key#MAKE}" ]; then
				echo "$key"
			fi
		done
	}
)
echo "Wiping vars:" $vars >&2
unset $vars
