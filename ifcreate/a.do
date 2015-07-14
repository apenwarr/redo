#!/bin/sh
if [ -e b ]; then
  redo-ifchange b
else
  redo-ifcreate b
fi
sleep 1
date +%s
