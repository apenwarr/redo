NL="
"

# Like 'echo', but never processes backslash escapes.
# (Some shells' builtin echo do, and some don't, so this
# is safer.)
xecho() {
	printf '%s\n' "$*"
}

# Returns true if string $1 contains the line $2.
# Lines are delimited by $NL.
contains_line() {
	case "$NL$1$NL" in
		*"$NL$2$NL"*) return 0 ;;
		*) return 1 ;;
	esac
}

# Split the first (up to) 20 words from $1,
# returning a string where the words are separated
# by $NL instead.
#
# To allow words including whitespace, you can backslash
# escape the whitespace (eg. hello\ world).  Backslashes
# will be removed from the output string.
#
# We can use this to read pkg-config output, among other
# things.
#
# TODO: find a POSIX sh way to eliminate the word limit.
#  I couldn't find an easy way to split on non-backslashed
#  whitespace without a fork-exec, which is too slow.
#  If we resorted to bashisms, we could use 'read -a',
#  but that's not portable.
rc_splitwords() {
	xecho "$1" | (
		read v0 v1 v2 v3 v4 v5 v6 v7 v8 v9 \
		     v10 v11 v12 v13 v14 v15 v16 v17 v18 v19 \
		     x
		if [ -n "$x" ]; then
			echo "rc_splitwords: too many words" >&2
			exit 97
		fi
		for d in "$v0" "$v1" "$v2" "$v3" "$v4" \
		         "$v5" "$v6" "$v7" "$v8" "$v9" \
		         "$v10" "$v11" "$v12" "$v13" "$v14" \
		         "$v15" "$v16" "$v17" "$v18" "$v19"; do
			[ -z "$d" ] || xecho "$d"
		done
	)
}

# Escape single-quote characters so they can
# be included as a sh-style single-quoted string.
shquote() {
	printf "'%s'" "$(xecho "$1" | sed -e "s,','\\\\'',g")"
}
