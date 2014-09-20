#!/bin/sh
if [ ! -e b ]; then
  redo-ifcreate b
fi
sleep 1
date +%s
