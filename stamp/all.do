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

echo 'date +%s | redo-stamp; sleep 1; date +%s' >c.do

redo-ifchange c
read c1 <c

redo-ifchange c
read c2 <c

echo 'sleep 1; date +%s' >c.do

redo-ifchange c
read c3 <c

redo-ifchange c
read c4 <c

if [ $c1 -lt $c2 ]; then
  echo 'PASS: c1 < c2' >&2
else
  echo 'FAIL: c1 > c2' >&2
fi

if [ $c3 -eq $c4 ]; then
  echo 'PASS: c3 = c4' >&2
else
  echo 'FAIL: c3 != c4' >&2
fi
