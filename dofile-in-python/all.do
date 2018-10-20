#!/usr/bin/env python3.5
from subprocess import run
from time import sleep

with open('source', 'w') as f:
    f.write('foo')

run(['redo-ifchange', 'target'])

with open('target', 'r') as f:
    target_contents_1 = f.read()

sleep(1)

with open('source', 'w') as f:
    f.write('bar')

run(['redo-ifchange', 'target'])

with open('target', 'r') as f:
    target_contents_2 = f.read()

if target_contents_1 == target_contents_2:
    exit(1)
