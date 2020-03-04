# Prerequisites

Currently, this version of redo requires python2.7 and the python2.7 sqlite3 module. 
Optional, but recommended, is the
[setproctitle](http://code.google.com/p/py-setproctitle/) module, which makes your
`ps` output prettier.

In modern versions of Debian, sqlite3 is already part of the python2.7 package. 
You can install the prerequisites like this:
```sh
	sudo apt-get install python2.7 python-setproctitle
```
(If you have install instructions for other OSes, please add them here :))


# Clone, compile, and test redo

You can run redo without installing it, like this:
```sh
	git clone https://github.com/apenwarr/redo
	cd redo
	./do -j10 test
```

If the tests pass, you can either add $PWD/redo/bin to your PATH, or install
redo on your system.  To install for all users, put it in /usr/local:

```sh
	DESTDIR= PREFIX=/usr/local sudo -E ./do install
```

Or to install it just for yourself (without needing root access), put it in
your home directory:
```sh
	DESTDIR= PREFIX=$HOME ./do install
```


# Pre-compiled packages

## MacOS

redo is available from the [Homebrew](https://brew.sh/) project:

	brew install redo

## Linux

Various linux distributions include redo under different names.  Most of the
packages are unfortunately obsolete and don't contain the most recent bug
fixes.  At this time (late 2018), we recommend using the latest tagged
version [from github](https://github.com/apenwarr/redo).
