#!/bin/sh
test -e b && rm b

redo-ifchange a
read a1 <a

date +%s >b
read b <b

redo-ifchange a
read a2 <a

if [ $a1 -le $a2 ]; then
  echo 'PASS: a1 <= a2' >&2
else
  echo 'FAIL: a1 > a2' >&2
fi

if [ $a1 -le $b ]; then
  echo 'PASS: a1 <= b' >&2
else
  echo 'FAIL: a1 > b' >&2
fi

if [ $a2 -le $b ]; then
  echo 'FAIL: a2 <= b' >&2
else
  echo 'PASS: a2 > b' >&2
fi
