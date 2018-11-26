for d in */all.do; do
    echo "${d%.do}"
done | xargs redo-ifchange
