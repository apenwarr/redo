redo-ifchange doc.list cookbook/all
sed 's/\.md/.1/' <doc.list |
xargs redo-ifchange

# mkdocs foolishly tries to process every file in this directory, which
# leads it to try to open temp files produced by the above redo-ifchange
# if it runs in parallel with those jobs.  So don't run it until they
# finish.
redo-ifchange mkdocs
