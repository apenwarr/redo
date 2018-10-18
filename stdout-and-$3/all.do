#!/bin/sh
redo-ifchange bogus \
 && printf >&2 'FAIL: Write to $3 and stdout possible.\n' \
 || printf >&2 'PASS: Write to $3 and stdout impossible.\n'
