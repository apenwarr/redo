#!/bin/sh
redo-ifchange a

read a <a
read b <b
read c <c

if [ $a -lt $b ]; then
  echo 'FAIL: a < b' >&2
else
  echo 'PASS: a > b' >&2
fi

if [ $a -lt $c ]; then
  echo 'FAIL: a < c' >&2
else
  echo 'PASS: a > c' >&2
fi
