#!/bin/sh
redo-ifchange a b

read a <a
read b <b
read c <c

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
