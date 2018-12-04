default: all

build:
	+./do build

all:
	+./do all

test:
	+./do test

clean:
	+./do clean

install:
	+./do install

env:
	env

.PHONY: build test clean env
