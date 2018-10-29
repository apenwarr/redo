for i in $(seq 10); do
  echo "$i.branch"
done | xargs redo-ifchange

