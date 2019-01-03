rm -f *~ .*~
for d in */clean.do; do
    echo "${d%.do}"
done | xargs redo
