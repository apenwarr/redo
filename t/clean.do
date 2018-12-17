/bin/ls [0-9s][0-9][0-9]*/clean.do |
sed 's/\.do$//' |
xargs redo

rm -f broken shellfile shelltest.warned shelltest.failed \
	*~ .*~ stress.log flush-cache
rm -rf 'space home dir'
