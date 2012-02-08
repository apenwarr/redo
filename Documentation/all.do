redo-ifchange md-file-list

sed 's/\.md/.1/' <md-file-list |
xargs redo-ifchange
