exec >&2

: ${INSTALL:=install}
: ${DESTDIR=NONE}
: ${PREFIX:=/usr}
: ${MANDIR:=$DESTDIR$PREFIX/share/man}
: ${DOCDIR:=$DESTDIR$PREFIX/share/doc/redo}
: ${BINDIR:=$DESTDIR$PREFIX/bin}
: ${LIBDIR:=$DESTDIR$PREFIX/lib/redo}

if [ "$DESTDIR" = "NONE" ]; then
	echo "$0: fatal: set DESTDIR before trying to install."
	exit 99
fi

redo-ifchange all redo/whichpython
read py <redo/whichpython

echo "Installing to: $DESTDIR$PREFIX"

# make dirs
for d in "$MANDIR/man1" "$DOCDIR" "$BINDIR" \
	"$LIBDIR" "$LIBDIR/version"
do
  if [ ! -d "$d" ]; then "$INSTALL" -d "$d"; fi
done

# docs
for d in docs/*.1; do
	[ "$d" = "docs/*.1" ] && continue
	"$INSTALL" -m 0644 $d "$MANDIR/man1"
done
"$INSTALL" -m 0644 README.md "$DOCDIR"

# .py files (precompiled to .pyc files for speed)
"$INSTALL" -m 0644 redo/*.py "$LIBDIR/"
"$INSTALL" -m 0644 redo/version/*.py "$LIBDIR/version/"
"$py" -mcompileall "$LIBDIR"

# It's important for the file to actually be named 'sh'.  Some shells (like
# bash and zsh) only go into POSIX-compatible mode if they have that name.
cp -R redo/sh "$LIBDIR/sh"

# binaries
bins=$(ls bin/redo* | grep '^bin/redo[-a-z]*$')
"$INSTALL" -m 0755 $bins "$BINDIR/"
