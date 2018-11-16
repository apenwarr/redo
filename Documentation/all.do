redo-ifchange doc.list
sed 's/\.md/.1/' <doc.list |
xargs redo-ifchange mkdocs
