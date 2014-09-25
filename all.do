#!/bin/sh
for dir in *; do
  if test -d $dir; then
    (cd $dir && redo)
  fi
done
