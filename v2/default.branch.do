for i in $(seq 100); do
 echo "$2$i.leaf"
done | xargs redo-ifchange
date +%s
