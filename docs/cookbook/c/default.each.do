# redo $2 in each of the registered output dirs.
# This way you can run commands or depend on targets like:
#    redo clean.each.do
#    redo all.each.do
# etc.
redo-ifchange allconfig

for dir in $(cat allconfig); do
	echo "$dir/$2"
done | xargs redo-ifchange
