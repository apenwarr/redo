#!/bin/sh
if timeout 1 redo-ifchange a; then
  echo 'PASS: limited recursion' >&2
else
  echo 'FAIL: unlimited recursion' >&2
fi
