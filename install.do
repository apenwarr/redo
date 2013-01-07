exec >&2
redo-ifchange _all

: ${INSTALL:=install}
: ${DESTDIR:=}
: ${PREFIX:=/usr}
: ${MANDIR:=$DESTDIR$PREFIX/share/man}
: ${DOCDIR:=$DESTDIR$PREFIX/share/doc/redo}
: ${BINDIR:=$DESTDIR$PREFIX/bin}
: ${LIBDIR:=$DESTDIR$PREFIX/lib/redo}

echo "Installing to: $DESTDIR$PREFIX"

# make dirs
$INSTALL -d $DOCDIR $BINDIR $LIBDIR $LIBDIR/version
test -e Documentation/redo.1 && $INSTALL -d $MANDIR/man1

# docs
for d in Documentation/*.1; do
	[ "$d" = "Documentation/*.1" ] && continue
	$INSTALL -m 0644 $d $MANDIR/man1
done
$INSTALL -m 0644 README.md $DOCDIR

# .py files (precompiled to .pyc files for speed)
for d in *.py version/*.py; do
	fix=$(echo $d | sed 's,-,_,g')
	$INSTALL -m 0644 $d $LIBDIR/$fix
done
python -mcompileall $LIBDIR

# It's important for the file to actually be named 'sh'.  Some shells (like
# bash and zsh) only go into POSIX-compatible mode if they have that name.
cp -R redo-sh/sh $LIBDIR/sh

# binaries
for dd in redo*.py; do
	d=$(basename $dd .py)
	fix=$(echo $d | sed -e 's,-,_,g')
	cat >install.wrapper <<-EOF
		#!/usr/bin/python
		import sys, os;
		exedir = os.path.dirname(os.path.abspath(sys.argv[0]))
		sys.path.insert(0, os.path.join(exedir, '../lib/redo'))
		import $fix
	EOF
	$INSTALL -m 0755 install.wrapper $BINDIR/$d
done
rm -f install.wrapper
