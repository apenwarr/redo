#!/bin/sh
redo-always
( md5sum <b || md5 <b ) | redo-stamp
sleep 1
date +%s
