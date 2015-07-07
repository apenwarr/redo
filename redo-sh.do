exec >&2
redo-ifchange t/shelltest.od

rm -rf $1.new $1/sh
mkdir $1.new

GOOD=/bin/bash

rm -rf $1 $1.new $3
mkdir $3
ln -s $GOOD $3/sh
