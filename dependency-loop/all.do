#!/bin/sh
set +e
timeout 1 redo-ifchange a
STATUS=$?
case $STATUS in
 1)
  echo 'PASS: limited recursion' >&2
 ;;
 124)
  echo 'FAIL: unlimited recursion' >&2
 ;;
esac
set -e