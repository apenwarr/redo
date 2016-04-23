#!/bin/sh
redo-ifchange a
read a1 <a

redo-ifchange a
read a2 <a

if [ $a1 -ge $a2 ]; then
  echo 'FAIL: a1 >= a2' >&2
else
  echo 'PASS: a1 < a2' >&2
fi
