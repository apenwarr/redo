# builds 1xx*/all
/bin/ls 1[0-9][0-9]*/all.do |
sed 's/\.do$//' |
xargs redo
110-compile/hello >&2

# builds the rest
/bin/ls [2-9][0-9][0-9]*/all.do |
sed 's/\.do$//' |
xargs redo-ifchange
