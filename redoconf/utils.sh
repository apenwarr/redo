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

# Split words from $@, returning a string where the words
# are separated by $NL instead.
#
# To allow words including whitespace, you can use the usual
# shell quoting mechanisms like backslash (\), single or
# double quotes.
#
# We can use this to read pkg-config output, among other
# things.
rc_splitwords() {
    eval "set -- $@"
    for w in "$@"; do
        [ -z "$w" ] || xecho "$w"
    done
}

# Escape single-quote characters so they can
# be included as a sh-style single-quoted string.
shquote() {
	printf "'%s'" "$(xecho "$1" | sed -e "s,','\\\\'',g")"
}
