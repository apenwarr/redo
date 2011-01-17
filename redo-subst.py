#!/usr/bin/python
import sys, os

if len(sys.argv) < 4:
	sys.exit(0)

fromsuffix = sys.argv[1]
tosuffix  = sys.argv[2]

for file in sys.argv[3:]:
	if file[-len(fromsuffix):] == fromsuffix:
		file = file[0:-len(fromsuffix)] + tosuffix
	print file
