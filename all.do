for dir in *; do
  if test -d $dir; then
    (cd $dir && redo all)
  fi
done
