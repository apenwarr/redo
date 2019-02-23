# This script starts with $PWD=output dir, $S=input dir.
REDOCONF="$S/redoconf"
if [ ! -d "$S" ] || [ ! -f "$REDOCONF/default.do.sh" ]; then
	echo "default.do.sh: \$S is not set correctly." >&2
	exit 99
fi
. "$REDOCONF/utils.sh"
RC_TARGET="$1"
rm -f "$RC_TARGET.log"

redo-ifchange "$REDOCONF/rc.sh" "$REDOCONF/utils.sh"

_rc_exit_check() {
	if [ -z "$RC_INCLUDE_RAN" ]; then
		echo "Fatal: used redoconf/rc.sh but didn't call rc_include." >&2
		exit 91
	elif [ -n "$RC_QUEUE" ]; then
		echo "Fatal: must call rc_save or rc_undo before ending." >&2
		exit 92
	fi
}
trap _rc_exit_check EXIT

rc_hook() {
	# nothing by default; can be overridden
	:
}

# Declare that a variable *named* $1 is used
# as input for the current script, and provide
# a help message in $2 for use with
# configure --help-flags.
helpmsg() {
	# Nothing to do by default
	rc_hook "$1"
}

# Assign the string $2 to the global variable
# *named* by $1.
replaceln() {
	rc_hook "$1"
	eval $1=\$2
}

# If $2 is nonempty, append a newline and $2 to
# the global variable *named* by $1
appendln() {
	rc_hook "$1"
	eval local tmp=\"\$$1\$NL\$2\"
	eval $1='${tmp#$NL}'
}

# Write a command line that calls "uses $1",
# including proper sh-escaping.
rc_helpmsg() {
	local cmd="helpmsg"
	cmd="helpmsg $1 $(shquote "$2")"
	eval "$cmd"
	appendln RC_HELP_QUEUE "$cmd"
}

_rc_record() {
	if ! contains_line "$RC_CHANGED" "$1"; then
		local oldv=
		eval oldv="\$$1"
		eval "old$1=\$oldv"
		RC_CHANGED="$RC_CHANGED$NL$1"
	fi
}

# Write a command line that calls "appendln $1 $2",
# including properly sh-escaping $2.
rc_appendln() {
	RC_LOG="$RC_LOG  $1 += $(shquote "$2")$NL"
	_rc_record "$1"
	local cmd="appendln $1 $(shquote "$2")"
	eval "$cmd"
	appendln RC_QUEUE "$cmd"
}

# Write a command line that replaces $1 with $2,
# including properly sh-escaping $2.
# This is good for variables like CC and CXX, where
# appending isn't what we want.
rc_replaceln() {
	RC_LOG="$RC_LOG  $1 = $(shquote "$2")$NL"
	_rc_record "$1"
	local cmd="replaceln $1 $(shquote "$2")"
	eval "$cmd"
	appendln RC_QUEUE "$cmd"
}

# Read compiler variables from _init.rc and the listed .rc files.
# Runs redo-ifchange to generate the .rc files as needed.
rc_include() {
	local d="" want="" target="$RC_TARGET" ops4="$PS4"
	RC_INCLUDE_RAN=1
	for d in rc/_init.rc "$@"; do
		if [ "$d" = "${d%.rc}" ]; then
			xecho "$0: rc_include: '$d' must end in .rc" >&2
			exit 99
		fi
		if ! contains_line "$RC_INCLUDES" "$d"; then
			want="$want$NL$d"
			RC_INCLUDES="$RC_INCLUDES$NL$d"
		fi
	done
	want="${want#$NL}"
	if [ -n "$want" ]; then
		xIFS="$IFS"
		IFS="$NL"
		set -f
		redo-ifchange $want
		for d in $want; do
			IFS="$xIFS"
			set +f
			RC_TARGET="$d"
			PS4="$PS4[$d] "
			[ ! -e "$d" ] || { :; . "./$d"; }
			PS4="$ops4"
		done
		IFS="$xIFS"
		set +f
	fi
	unset RC_QUEUE
	PS4="$ops4"
	RC_TARGET="$target"
}

# Undo the currently enqueued rc_appendln and rc_replaceln
# actions, restoring the affected variables back to their
# original values.
rc_undo() {
	local xIFS="$IFS" v=
	IFS="$NL"
	for k in $RC_CHANGED; do
		eval v="\$old$k"
		eval "$k=\$v"
	done
	unset RC_CHANGED
	unset RC_QUEUE
	unset RC_LOG
}

# Write the currently active rc_include,
# rc_replaceln, and rc_appendln commands to stdout,
# to produce the final .rc file.
rc_save() {
	printf '%s' "${RC_LOG}" >&2
	if [ -n "$RC_INCLUDES" ]; then
		(
			xIFS="$IFS"
			IFS="$NL"
			printf 'rc_include '
			for d in $RC_INCLUDES; do
				printf '%s ' "$d"
			done
			printf '\n'
		)
	fi
	xecho "$RC_HELP_QUEUE"
	xecho "$RC_QUEUE"
	unset RC_QUEUE
	unset RC_CHANGED
}

rc_compile() {
	redo-ifchange "$REDOCONF/trycompile"
	( . "$REDOCONF/trycompile" "$@" ) >>"$RC_TARGET.log" 2>&1
}

_pkg_config() {
	(
		IFS="$NL"
		set -f
		$PKG_CONFIG $PKG_CONFIG_FLAGS "$@"
	)
}

_rc_pkg_add() {
	local var="$1" vvar= want=
	shift
	if [ -n "$HAVE_PKG_CONFIG" ]; then
		for d in "$@"; do
			if _pkg_config --exists "$d"; then
				want="$want $d"
			fi
		done
		if [ -n "$want" ]; then
			rc_appendln CPPFLAGS \
				"$(rc_splitwords \
				    "$(_pkg_config --cflags $want)")"
			vvar="$(rc_splitwords \
			    "$(_pkg_config --libs $want)")"
			rc_appendln "$var" "$vvar"
		fi
	else
		echo "(pkg-config is missing)" >&2
	fi
}

# Determine whether packages listed in $2 all exists and are functional,
# by finding them using pkg-config and running the command in $3..$n.
#
# If the package works:
#   HAVE_$1 is set to 1
#   CPPFLAGS and the variable named by $1 are updated with compiler and
#      linker flags, respectively.
# else:
#   HAVE_$1 is set to blank.
#
# Returns success in either case.  Check detection results in the
# HAVE_$1 variable if needed.
rc_pkg_detect() {
	if ! contains_line "$RC_INCLUDES" rc/pkg-config.rc; then
		echo "Error: include pkg-config.rc before using rc_pkg_*" >&2
		return 1
	fi
	if [ "$#" -lt 3 ]; then
		echo "Error: rc_pkg_detect needs a command to test." >&2
		return 1
	fi
	local var="$1" vvar="" pkgs="$2"
	shift
	shift
	eval vvar="\$$var"
	rc_helpmsg "$var" "Extra linker options for '$pkgs'"
	if [ -z "$vvar" ]; then
		_rc_pkg_add "$var" $pkgs
		eval vvar="\$$var"
	fi
	appendln LIBS "$vvar"
	if ("$@"); then
		rc_replaceln "HAVE_$var" 1
	else
		rc_undo
		rc_replaceln "HAVE_$var" ""
		rc_replaceln "$var" ""
	fi
}
