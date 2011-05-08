% redo-ifchange(1) Redo %VERSION%
% Avery Pennarun <apenwarr@gmail.com>
% %DATE%

# NAME

redo-ifchange - rebuild target files when source files have changed

# SYNOPSIS

redo-ifchange [targets...]


# DESCRIPTION

Normally redo-ifchange is run from a .do file that has been
executed by `redo`(1).  See `redo`(1) for more details.

redo-ifchange doesn't take any command line options other
than a list of *targets*.  To provide command line options,
you need to run `redo` instead.

redo-ifchange performs the following steps:

- it creates a dependency on the given *targets*.  If any
  of those targets change in the future, the current target
  (the one calling redo-ifchange) will marked as needing to
  be rebuilt.
  
- for any *target* that is out of date, it calls the
  equivalent of `redo target`.

- for any *target* that is locked (because some other
  instance of `redo` or `redo-ifchange` is already building
  it), it waits until the lock is released.
  
redo-ifchange returns only after all the given
*targets* are known to be up to date.


# TIP 1

You don't have to run redo-ifchange *before* generating
your target; you can generate your target first, then
declare its dependencies.  For example, as part of
compiling a .c file, gcc learns the list
of .h files it depends on. You can pass this information
along to redo-ifchange, so if any of those headers are
changed or deleted, your .c file will be rebuilt:

        redo-ifchange $1.c
        gcc -o $3 -c $1.c \
            -MMD -MF $1.deps
        read DEPS <$1.deps
        redo-ifchange ${DEPS#*:}

This is much less confusing than the equivalent
autodependency mechanism in `make`(1), because make
requires that you declare all your dependencies before
running the target build commands.


# TIP 2

Try to list as many dependencies as possible in a single
call to redo-ifchange.  Every time you run redo-ifchange,
the shell has to fork+exec it, which takes time.  Plus redo
can only parallelize your build if you give it multiple
targets to build at once.  It's fine to have a couple of
separate redo-ifchange invocations for a particular target
when necessary (as in TIP 1 above), but try to keep it to a
minimum.  For example here's a trick for generating a list
of targets, but redo-ifchanging them all at once:

	for d in *.c; do
		echo ${d%.c}.o
	done |
	xargs redo-ifchange


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-ifcreate`(1), `redo-always`(1), `redo-stamp`(1)
