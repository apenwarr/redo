# This script starts with $PWD=output dir, $S=input dir.
read -r S <src
REDOCONF="$S/redoconf"
if [ ! -d "$S" ] || [ ! -f "$REDOCONF/default.do.sh" ]; then
	echo "default.do.sh: \$S is not set correctly." >&2
	exit 99
fi

NL="
"

_mkdir_of() {
	local dir="${1%/*}"
	[ "$dir" = "$1" ] ||
	[ -z "$dir" ] ||
	[ -d "$dir" ] ||
	mkdir -p "$dir"
}

# Delegate to .od files specifically for this target, if any.
_base1=${1##*/}
_dir1=${1%"$_base1"}
_missing=""
for d in "$S/$1.od" \
         "$S/${_dir1}default.${_base1#*.}.od" \
         "$REDOCONF/$1.od" \
         "$REDOCONF/${_dir1}default.${_base1#*.}.od"; do
	if [ -e "$d" ]; then
		redo-ifchange "$d"
		_mkdir_of "$3"
		( PS4="$PS4[$d] "; . "$d" )
		exit
	else
		missing="$missing$NL$d"
	fi
done

_add_missing() {
	[ -n "$missing" ] && (IFS="$NL"; set -f; redo-ifcreate $missing)
	missing=
}

_pick_src() {
	# Look for the source file corresponding to a given .o file.
	# If the source file is missing, we can also build it from
	# eg. a .c.do script.
	#
	# Returns the matching source file in $src, the compiler
	# mode in $lang, and appends any redo-ifcreate targets to
	# $missing.
	lang=cc
	for src in "$1.c"; do
		[ -e "$src" ] && return
		[ -e "$src.do" ] && return
		missing="$missing$NL$src"
	done
	lang=cxx
	for src in "$1.cc" "$1.cpp" "$1.cxx" "$1.C" "$1.c++"; do
		[ -e "$src" ] && return
		[ -e "$src.do" ] && return
		missing="$missing$NL$src"
	done
	echo "default.do.sh: _pick_src: no source file found for '$1.*'" >&2
	return 1
}

_objlist() {
	local suffix="$1" list="$2"
	local base="${2##*/}"
	local dir="${2%"$base"}"
	while read -r d; do
		case $d in
			-*) ;;
			*.c|*.cc|*.cpp|*.cxx|*.C|*.c++)
				echo "$dir${d%.*}$suffix"
				;;
			*) echo "$dir$d" ;;
		esac
	done <"$list"
}

_flaglist() {
	while read -r d; do
		[ "$d" != "${d#-}" ] || continue
		echo "$d"
	done <"$1"
}

compile() {
	redo-ifchange compile "$src" $dep
	rm -f "$1.deps"
	_mkdir_of "$3"
	xCFLAGS="$xCFLAGS" PCH="$PCH" ./compile "$3" "$1.deps" "$src"
	# TODO: make work with dependency filenames containing whitespace.
	#   gcc writes whitespace-containing filenames with spaces
	#   prefixed by backslash.  read (without -r) will remove the
	#   backslashes but still use spaces for word splitting, so
	#   it loses the distinction.  rc_splitwords() is the right
	#   function, but currently has a max word limit.
	read deps <"$2.deps"
	redo-ifchange ${deps#*:}
}

case $1 in
    *.fpic.o)
	_pick_src "$S/${1%.fpic.o}"
	_add_missing
	xCFLAGS="-fPIC" PCH="2" dep="$lang-fpic.precompile" compile "$@"
	exit  # fast path: exit as early as possible
	;;
    *.o)
	_pick_src "$S/${1%.o}"
	_add_missing
	xCFLAGS="" PCH="1" dep="$lang.precompile" compile "$@"
	exit  # fast path: exit as early as possible
	;;
    *.h.fpic.gch|*.hpp.fpic.gch)
	src="$S/${1%.fpic.gch}"
	xCFLAGS="-fPIC" PCH="3" dep="" compile "$@"
	# precompiled header is "unchanged" if its component
	# headers are unchanged.
	cat ${deps#*:} | tee $1.stamp | redo-stamp
	;;
    *.h.gch|*.hpp.gch)
	src="$S/${1%.gch}"
	xCFLAGS="" PCH="3" dep="" compile "$@"
	# precompiled header is "unchanged" if its component
	# headers are unchanged.
	cat ${deps#*:} | tee $1.stamp | redo-stamp
	;;
    *.a)
	listf="${1%.a}.list"
	redo-ifchange "$listf"
	files=$(_objlist .o "$listf")
	IFS="$NL"
	redo-ifchange $files
	ar q "$3" $files
	;;
    *.so)
	verf="${1%.so}.ver"
	listf="${1%.so}.list"
	redo-ifchange link-shlib "$verf" "$listf"
	read ver <"$verf"
	files=$(_objlist .fpic.o "$listf")
	xLIBS=$(_flaglist "$listf")
	IFS="$NL"
	redo-ifchange $files
	xLIBS="$xLIBS" ./link-shlib "$1.$ver" $files
	ln -s "$(basename "$1.$ver")" "$3"
	ln -sf "$1.$ver" .
	;;
    *.list|*.ver)
	if [ -e "$S/$1" ]; then
		redo-ifchange "$S/$1"
		_mkdir_of "$3"
		cp "$S/$1" "$3"
	else
		echo "default.do.sh: no rule to build '$1'" >&2
		exit 99
	fi
	;;
    *)
	# In unix, binary names typically don't have any special filename
	# pattern, so we have to handle them in a catch-all here.
	# We detect that it's intended as a binary, and not just a typo,
	# by the existence of a .list or .list.od file with the same name,
	# defining the list of input files.
	#
	# Some people like to name their binaries *.exe, eg. on Windows,
	# even though that doesn't matter anymore, even on Windows.
	# So use the same rules for generating a .exe as a non-.exe.
	bin="${1%.exe}"
	if [ -e "$S/$bin.list" -o -e "$S/$bin.list.od" ]; then
		# a final program binary
		redo-ifchange link "$bin.list"
		files=$(_objlist .o "$bin.list")
		xLIBS=$(_flaglist "$bin.list")
		IFS="$NL"
		redo-ifchange $files
		xLIBS="$xLIBS" ./link "$3" $files
	else
		echo "default.do.sh: no rule to build '$1' or '$1.list'" >&2
		exit 99
	fi
	;;
esac
