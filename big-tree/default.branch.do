#!/bin/sh
for i in $(seq 100); do
 redo-ifchange $2$i.leaf
done
date +%s
