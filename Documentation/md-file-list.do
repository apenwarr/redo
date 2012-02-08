redo-always
/bin/ls *.md t/*.md |
sed 's/\.md/.1/' >$3
redo-stamp <$3
