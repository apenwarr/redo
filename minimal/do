#!/usr/bin/env sh
#
# A minimal alternative to djb redo that doesn't support incremental builds.
# For the full version, visit http://github.com/apenwarr/redo
#
# The author disclaims copyright to this source file and hereby places it in
# the public domain. (2010 12 14; updated 2019 02 24)
#
USAGE="
usage: do [-d] [-x] [-v] [-c] <targets...>
  -d  print extra debug messages (mostly about dependency checks)
  -v  run .do files with 'set -v'
  -x  run .do files with 'set -x'
  -c  clean up all old targets before starting

  Note: do is an implementation of redo that does *not* check dependencies.
  It will never rebuild a target it has already built, unless you use -c.
"

# CDPATH apparently causes unexpected 'cd' output on some platforms.
unset CDPATH

# By default, no output coloring.
green=""
bold=""
plain=""

if [ -n "$TERM" -a "$TERM" != "dumb" ] && tty <&2 >/dev/null 2>&1; then
	green="$(printf '\033[32m')"
	bold="$(printf '\033[1m')"
	plain="$(printf '\033[m')"
fi

# The 'seq' command is not available on all platforms.
_seq() {
	local x=0 max="$1"
	while [ "$x" -lt "$max" ]; do
		x=$((x + 1))
		echo "$x"
	done
}

# Split $1 into a dir part ($_dirsplit_dir) and base filename ($_dirsplit_base)
_dirsplit() {
	_dirsplit_base=${1##*/}
	_dirsplit_dir=${1%$_dirsplit_base}
}

# Like /usr/bin/dirname, but avoids a fork and uses _dirsplit semantics.
qdirname() (
	_dirsplit "$1"
	dir=${_dirsplit_dir%/}
	echo "${dir:-.}"
)

_dirsplit "$0"
REDO=$(cd "$(pwd -P)" &&
	cd "${_dirsplit_dir:-.}" &&
	echo "$PWD/$_dirsplit_base")
export REDO
_cmd=$_dirsplit_base

DO_TOP=
if [ -z "$DO_BUILT" ]; then
	export _do_opt_debug=
	export _do_opt_exec=
	export _do_opt_verbose=
	export _do_opt_clean=
fi
while getopts 'dxvcj:h?' _opt; do
	case $_opt in
		d) _do_opt_debug=1 ;;
		x) _do_opt_exec=x ;;
		v) _do_opt_verbose=v ;;
		c) _do_opt_clean=1 ;;
		j) ;;  # silently ignore, for compat with real redo
		\?|h|*) printf "%s" "$USAGE" >&2
		   exit 99
		   ;;
	esac
done
shift "$((OPTIND - 1))"
_debug() {
	[ -z "$_do_opt_debug" ] || echo "$@" >&2
}

if [ -z "$DO_BUILT" -a "$_cmd" != "redo-whichdo" ]; then
	DO_TOP=1
	if [ "$#" -eq 0 ] && [ "$_cmd" = "do" -o "$_cmd" = "redo" ]; then
		set all  # only toplevel redo has a default target
	fi
	export DO_STARTDIR="$(pwd -P)"
	# If starting /bin/pwd != $PWD, this will fix it.
	# That can happen when $PWD contains symlinks that the shell is
	# trying helpfully (but unsuccessfully) to hide from the user.
	cd "$DO_STARTDIR" || exit 99
	export DO_BUILT="$PWD/.do_built"
	if [ -z "$_do_opt_clean" -a -e "$DO_BUILT" ]; then
		echo "do: Incremental mode. Use -c for clean rebuild." >&2
	fi
	: >>"$DO_BUILT"
	sort -u "$DO_BUILT" >"$DO_BUILT.new"
	while read f; do
		[ -n "$_do_opt_clean" ] && printf "%s\0%s.did\0" "$f" "$f"
		printf "%s.did.tmp\0" "$f"
	done <"$DO_BUILT.new" |
	xargs -0 rm -f 2>/dev/null
	mv "$DO_BUILT.new" "$DO_BUILT"
	export DO_PATH="$DO_BUILT.dir"
	export PATH="$DO_PATH:$PATH"
	rm -rf "$DO_PATH"
	mkdir "$DO_PATH"
	for d in redo redo-ifchange redo-whichdo; do
		ln -s "$REDO" "$DO_PATH/$d"
	done
	for d in redo-ifcreate redo-stamp redo-always redo-ood \
	    redo-targets redo-sources; do
	        echo "#!/bin/sh" >"$DO_PATH/$d"
		chmod a+rx "$DO_PATH/$d"
	done
fi


# Chop the "file" part off a /path/to/file pathname.
# Note that if the filename already ends in a /, we just remove the slash.
_updir()
{
	local v="${1%/*}"
	[ "$v" != "$1" ] && echo "$v"
	# else "empty" which means we went past the root
}


# Returns true if $1 starts with $2.
_startswith()
{
	[ "${1#"$2"}" != "$1" ]
}


# Returns true if $1 ends with $2.
_endswith()
{
	[ "${1%"$2"}" != "$1" ]
}


# Prints $1 if it's absolute, or $2/$1 if $1 is not absolute.
_abspath()
{
	local here="$2" there="$1"
	if _startswith "$1" "/"; then
		echo "$1"
	else
		echo "$2/$1"
	fi
}


# Prints $1 as a path relative to $PWD (not starting with /).
# If it already doesn't start with a /, doesn't change the string.
_relpath()
{
	local here="$2" there="$1" out= hadslash=
	#echo "RP start '$there' hs='$hadslash'" >&2
	_startswith "$there" "/" || { echo "$there" && return; }
	[ "$there" != "/" ] && _endswith "$there" "/" && hadslash=/
	here=${here%/}/
	while [ -n "$here" ]; do
		#echo "RP out='$out' here='$here' there='$there'" >&2
		[ "${here%/}" = "${there%/}" ] && there= && break;
		[ "${there#$here}" != "$there" ] && break
		out=../$out
		_dirsplit "${here%/}"
		here=$_dirsplit_dir
	done
	there=${there#$here}
	if [ -n "$there" ]; then
		echo "$out${there%/}$hadslash"
	else
		echo "${out%/}$hadslash"
	fi
}


# Prints a "normalized relative" path, with ".." resolved where possible.
# For example, a/b/../c will be reduced to just a/c.
_normpath()
(
	local path="$1" relto="$2" out= isabs=
	#echo "NP start '$path'" >&2
	if _startswith "$path" "/"; then
		isabs=1
	else
		path="${relto%/}/$path"
	fi
	set -f
	IFS=/
	for d in ${path%/}; do
		#echo "NP out='$out' d='$d'" >&2
		if [ "$d" = ".." ]; then
			out=$(_updir "${out%/}")/
		else
			out=$out$d/
		fi
	done
	#echo "NP out='$out' (done)" >&2
	out=${out%/}
	if [ -n "$isabs" ]; then
		echo "${out:-/}"
	else
		_relpath "${out:-/}" "$relto"
	fi
)


# Prints a "real" path, with all symlinks resolved where possible.
_realpath()
{
	local path="$1" relto="$2" isabs= rest=
	if _startswith "$path" "/"; then
		isabs=1
	else
		path="${relto%/}/$path"
	fi
	(
		for d in $(_seq 100); do
			#echo "Trying: $PWD--$path" >&2
			if cd -P "$path" 2>/dev/null; then
				# success
				pwd=$(pwd -P)
				#echo "  chdir ok: $pwd--$rest" >&2
				np=$(_normpath "${pwd%/}/$rest" "$relto")
				if [ -n "$isabs" ]; then
					echo "$np"
				else
					_relpath "$np" "$relto"
				fi
				break
			fi
			_dirsplit "${path%/}"
			path=$_dirsplit_dir
			rest="$_dirsplit_base/$rest"
		done
	)
}


# List the possible names for default*.do files in dir $1 matching the target
# pattern in $2.  We stop searching when we find the first one that exists.
_find_dofiles_pwd()
{
	local dodir="$1" dofile="$2"
	_startswith "$dofile" "default." || dofile=${dofile#*.}
	while :; do
		dofile=default.${dofile#default.*.}
		echo "$dodir$dofile"
		[ -e "$dodir$dofile" ] && return 0
		[ "$dofile" = default.do ] && break
	done
	return 1
}


# List the possible names for default*.do files in $PWD matching the target
# pattern in $1.  We stop searching when we find the first name that works.
# If there are no matches in $PWD, we'll search in .., and so on, to the root.
_find_dofiles()
{
	local target="$1" dodir= dofile= newdir=
	_debug "find_dofile: '$PWD' '$target'"
	dofile="$target.do"
	echo "$dofile"
	[ -e "$dofile" ] && return 0

	# Try default.*.do files, walking up the tree
	_dirsplit "$dofile"
	dodir=$_dirsplit_dir
	dofile=$_dirsplit_base
	[ -n "$dodir" ] && dodir=${dodir%/}/
	[ -e "$dodir$dofile" ] && return 0
	for i in $(_seq 100); do
		[ -n "$dodir" ] && dodir=${dodir%/}/
		#echo "_find_dofiles: '$dodir' '$dofile'" >&2
		_find_dofiles_pwd "$dodir" "$dofile" && return 0
		newdir=$(_realpath "${dodir}.." "$PWD")
		[ "$newdir" = "$dodir" ] && break
		dodir=$newdir
	done
	return 1
}


# Print the last .do file returned by _find_dofiles.
# If that file exists, returns 0, else 1.
_find_dofile()
{
	local files="$(_find_dofiles "$1")"
	rv=$?
	#echo "files='$files'" >&2
	[ "$rv" -ne 0 ] && return $rv
	echo "$files" | {
		while read -r linex; do line=$linex; done
		printf "%s\n" "$line"
	}
}


# Actually run the given $dofile with the arguments in $@.
# Note: you should always run this in a subshell.
_run_dofile()
{
	export DO_DEPTH="$DO_DEPTH  "
	export REDO_TARGET="$PWD/$target"
	local line1
	set -e
	read line1 <"$PWD/$dofile" || true
	cmd=${line1#"#!/"}
	if [ "$cmd" != "$line1" ]; then
		set -$_do_opt_verbose$_do_opt_exec
		exec /$cmd "$PWD/$dofile" "$@"
	else
		set -$_do_opt_verbose$_do_opt_exec
		# If $dofile is empty, "." might not change $? at
		# all, so we clear it first with ":".
		:; . "$PWD/$dofile"
	fi
}


# Find and run the right .do file, starting in dir $1, for target $2,
# providing a temporary output file as $3.  Renames the temp file to $2 when
# done.
_do()
{
	local dir="$1" target="$1$2" tmp="$1$2.redo.tmp" tdir=
	local dopath= dodir= dofile= ext=
	if [ "$_cmd" = "redo" ] ||
	    ( [ ! -e "$target" -o -d "$target" ] &&
	      [ ! -e "$target.did" ] ); then
		printf '%sdo  %s%s%s%s\n' \
			"$green" "$DO_DEPTH" "$bold" "$target" "$plain" >&2
		dopath=$(_find_dofile "$target")
		if [ ! -e "$dopath" ]; then
			echo "do: $target: no .do file ($PWD)" >&2
			return 1
		fi
		_dirsplit "$dopath"
		dodir=$_dirsplit_dir dofile=$_dirsplit_base
		if _startswith "$dofile" "default."; then
			ext=${dofile#default}
			ext=${ext%.do}
		else
			ext=
		fi
		target=$PWD/$target
		tmp=$PWD/$tmp
		cd "$dodir" || return 99
		target=$(_relpath "$target" "$PWD") || return 98
		tmp=$(_relpath "$tmp" "$PWD") || return 97
		base=${target%$ext}
		tdir=$(qdirname "$target")
		[ ! -e "$DO_BUILT" ] || [ ! -w "$tdir/." ] ||
		: >>"$target.did.tmp"
		# $qtmp is a temporary file used to capture stdout.
		# Since it might be accidentally deleted as a .do file
		# does its work, we create it, then open two fds to it,
		# then immediately delete the name.  We use one fd to
		# redirect to stdout, and the other to read from after,
		# because there's no way to fseek(fd, 0) in sh.
		qtmp=$DO_PATH/do.$$.tmp
		(
			rm -f "$qtmp"
			( _run_dofile "$target" "$base" "$tmp" >&3 3>&- 4<&- )
			rv=$?
			if [ $rv != 0 ]; then
				printf "do: %s%s\n" "$DO_DEPTH" \
					"$target: got exit code $rv" >&2
				rm -f "$tmp.tmp" "$tmp.tmp2" "$target.did"
				return $rv
			fi
			echo "$PWD/$target" >>"$DO_BUILT"
			if [ ! -e "$tmp" ]; then
				# if $3 wasn't created, copy from stdout file
				cat <&4 >$tmp
				# if that's zero length too, forget it
				[ -s "$tmp" ] || rm -f "$tmp"
			fi
		) 3>$qtmp 4<$qtmp  # can't use "|| return" here...
		# ...because "|| return" would mess up "set -e" inside the ()
		# on some shells.  Running commands in "||" context, even
		# deep inside, will stop "set -e" from functioning.
		rv=$?
		[ "$rv" = 0 ] || return "$rv"
		mv "$tmp" "$target" 2>/dev/null
		[ -e "$target.did.tmp" ] &&
		mv "$target.did.tmp" "$target.did" ||
		: >>"$target.did"
	else
		_debug "do  $DO_DEPTH$target exists." >&2
	fi
}


# Implementation of the "redo" command.
_redo()
{
	local i startdir="$PWD" dir base
	set +e
	for i in "$@"; do
		i=$(_abspath "$i" "$startdir")
		(
			cd "$DO_STARTDIR" || return 99
			i=$(_realpath "$(_relpath "$i" "$PWD")" "$PWD")
			_dirsplit "$i"
			dir=$_dirsplit_dir base=$_dirsplit_base
			_do "$dir" "$base"
		)
		[ "$?" = 0 ] || return 1
	done
}


# Implementation of the "redo-whichdo" command.
_whichdo()
{
	_find_dofiles "$1"
}


case $_cmd in
	do|redo|redo-ifchange) _redo "$@" ;;
	redo-whichdo) _whichdo "$1" ;;
	do.test) ;;
	*) printf "do: '%s': unexpected redo command" "$_cmd" >&2; exit 99 ;;
esac
[ "$?" = 0 ] || exit 1

if [ -n "$DO_TOP" ]; then
	if [ -n "$_do_opt_clean" ]; then
		echo "do: Removing stamp files..." >&2
		[ ! -e "$DO_BUILT" ] ||
		while read f; do printf "%s.did\0" "$f"; done <"$DO_BUILT" |
		xargs -0 rm -f 2>/dev/null
	fi
fi
