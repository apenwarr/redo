/bin/ls *.md |
sed 's/\.md/.1/' |
xargs redo-ifchange

redo-always
