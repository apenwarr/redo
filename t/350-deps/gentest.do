rm -f genfile2 genfile2.do genfile.log

echo echo hello >genfile2.do
../flush-cache
redo genfile1

# this will cause a rebuild:
#      genfile1 depends on genfile2 depends on genfile2.do
rm -f genfile2.do
../flush-cache
redo-ifchange genfile1

# but genfile2.do was gone last time, so genfile2 no longer depends on it.
# thus, it can be considered up-to-date.  Prior versions of redo had a bug
# where the dependency on genfile2.do was never dropped.
../flush-cache
redo-ifchange genfile1

COUNT=$(wc -l <genfile.log)
. ../skip-if-minimal-do.sh
[ "$COUNT" -eq 2 ] || exit 77
