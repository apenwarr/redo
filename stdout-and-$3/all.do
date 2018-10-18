#!/bin/sh
[ -e stdout ] && rm stdout
redo-ifchange stdout
read -r STDOUT <stdout
[ "${STDOUT}" = "stdout" ] \
 && printf >&2 'PASS: Write to stdout possible.\n' \
 || printf >&2 'FAIL: Write to stdout impossible.\n'

[ -e param3 ] && rm param3
redo-ifchange param3
read -r PARAM3 <param3
[ "${PARAM3}" = "param3" ] \
 && printf >&2 'PASS: Write to $3 possible.\n' \
 || printf >&2 'FAIL: Write to $3 impossible.\n'

redo-ifchange bogus \
 && printf >&2 'FAIL: Write to $3 and stdout possible.\n' \
 || printf >&2 'PASS: Write to $3 and stdout impossible.\n'
