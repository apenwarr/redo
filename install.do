exec >&2
redo-ifchange Documentation/all

: ${INSTALL:=install}
: ${DESTDIR:=}
: ${PREFIX:=/usr}
: ${MANDIR:=$DESTDIR$PREFIX/share/man}
: ${DOCDIR:=$DESTDIR$PREFIX/share/doc/redo}
: ${BINDIR:=$DESTDIR$PREFIX/bin}
: ${LIBDIR:=$DESTDIR$PREFIX/lib/redo}

echo "Installing to: $DESTDIR$PREFIX"

# make dirs
$INSTALL -d $MANDIR/man1 $DOCDIR $BINDIR $LIBDIR

# docs
for d in Documentation/*.1; do
	[ "$d" = "Documentation/*.1" ] && continue
	$INSTALL -m 0644 $d $MANDIR/man1
done
$INSTALL -m 0644 README.md $DOCDIR

# .py files (precompiled to .pyc files for speed)
for d in *.py; do
	fix=$(echo $d | sed 's,-,_,g')
	$INSTALL -m 0644 $d $LIBDIR/$fix
done
python -mcompileall $LIBDIR

# binaries
for d in redo redo-ifchange redo-ifcreate redo-always redo-stamp redo-oob; do
	fix=$(echo $d | sed 's,-,_,g')
	cat >install.wrapper <<-EOF
		#!/usr/bin/python
		import sys;
		sys.path.insert(0, '$LIBDIR')
		import $fix
	EOF
	$INSTALL -m 0755 install.wrapper $BINDIR/$d
done
rm -f install.wrapper
