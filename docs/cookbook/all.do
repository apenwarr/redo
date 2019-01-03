export NO_SLOW_TESTS=1
for d in */all.do; do
    echo "${d%.do}"
done | xargs redo-ifchange
