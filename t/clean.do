/bin/ls [0-9][0-9][0-9]*/clean.do |
sed 's/\.do$//' |
xargs redo

rm -f broken shellfile *~ .*~
