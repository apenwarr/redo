#!/bin/sh
echo 1 > b
redo-ifchange a
read a1 <a

echo 2 > b
redo-ifchange a
read a2 <a

echo 2 > b
redo-ifchange a
read a3 <a

if [ $a1 -lt $a2 ]; then
  echo 'PASS: a1 < a2' >&2
else
  echo 'FAIL: a1 > a2' >&2
fi

if [ $a2 -eq $a3 ]; then
  echo 'PASS: a2 = a3' >&2
else
  echo 'FAIL: a2 != a3' >&2
fi
