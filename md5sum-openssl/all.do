#!/bin/sh
export REDO_MD5SUM="openssl md5 -r"

echo 1 > b
redo-ifchange a
read a1 < a

echo 2 > b
redo-ifchange a
read a2 < a

: >> b
redo-ifchange a
read a3 < a

echo 3 > b

if [ $a1 -ge $a2 ]; then
  echo 'FAIL: a1 >= a2' >&2
else
  echo 'PASS: a1 < a2' >&2
fi

if [ $a2 != $a3 ]; then
  echo 'FAIL: a2 != a3' >&2
else
  echo 'PASS: a2 = a3' >&2
fi
