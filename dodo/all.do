#!/bin/sh
redo-ifchange a.do
redo-ifchange a

sleep 1
read a <a
now=$(date +%s)

if [ $a -lt $now ]; then
  echo 'PASS: a < now' >&2
else
  echo 'FAIL: a > now' >&2
fi
