#!/bin/sh
for i in $(seq 10); do
  redo-ifchange $i.branch
done
