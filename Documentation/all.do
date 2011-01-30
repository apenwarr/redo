/bin/ls *.md t/*.md |
sed 's/\.md/.1/' |
xargs redo-ifchange

redo-always
