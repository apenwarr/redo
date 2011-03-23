redo example/clean curse/clean deps/clean "space dir/clean" stamp/clean \
	defaults-flat/clean defaults-nested/clean autosubdir/clean
rm -f broken nonshelltest shellfile mode1 makedir.log chdir1 deltest2 \
	hello [by]ellow *.o *~ .*~ *.log CC LD passfail silence silence.do \
	touch1 touch1.do always1 ifcreate[12].dep ifcreate[12] *.vartest \
	atime2
rm -rf makedir
