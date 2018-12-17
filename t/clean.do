/bin/ls [0-9s][0-9][0-9]*/clean.do |
sed 's/\.do$//' |
xargs redo

rm -f broken shellfile shellfail shelltest.warned shelltest.failed shlink \
	*~ .*~ stress.log flush-cache 'symlink path'
rm -rf 'space home dir'
