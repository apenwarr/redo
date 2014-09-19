#!/bin/sh
redo-ifchange a b

read a <a
read b <b
read c <c
read d <d

if [ $a -lt $c ]; then
  echo 'FAIL: a < c' >&2
else
  echo 'PASS: a > c' >&2
fi

if [ $b -lt $c ]; then
  echo 'FAIL: b < c' >&2
else
  echo 'PASS: b > c' >&2
fi

if [ $a -lt $d ]; then
  echo 'FAIL: a < d' >&2
else
  echo 'PASS: a > d' >&2
fi

if [ $b -lt $d ]; then
  echo 'FAIL: b < d' >&2
else
  echo 'PASS: b > d' >&2
fi

if [ $c -lt $d ]; then
  echo 'FAIL: c < d' >&2
else
  echo 'PASS: c > d' >&2
fi
