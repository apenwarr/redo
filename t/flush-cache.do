redo-ifchange ../redo/whichpython $1.in
read py <../redo/whichpython
(
	echo "#!$py"
	cat $1.in
) >$3
chmod a+x $3
