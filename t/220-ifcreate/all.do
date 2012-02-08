rm -f exists ifcreate[12] ifcreate[12].log ifcreate[12].dep
. ../skip-if-minimal-do.sh
touch exists
redo-ifcreate exists 2>/dev/null && exit 91
rm exists
redo-ifcreate exists || exit 92

for d in 1 2; do
	redo ifcreate$d
	[ "$(wc -l <ifcreate$d.log)" -eq 1 ] || exit ${d}1
	redo-ifchange ifcreate$d
	[ "$(wc -l <ifcreate$d.log)" -eq 1 ] || exit ${d}2
	../flush-cache
	touch ifcreate$d.dep
	redo-ifchange ifcreate$d
	[ "$(wc -l <ifcreate$d.log)" -eq 2 ] || exit ${d}3
	../flush-cache
	rm ifcreate$d.dep
	redo-ifchange ifcreate$d
	[ "$(wc -l <ifcreate$d.log)" -eq 3 ] || exit ${d}4
done
