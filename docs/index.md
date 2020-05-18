# redo: a recursive, general-purpose build system

`redo` is a competitor to the long-lived, but sadly imperfect, `make`
program.  Unlike other such competitors, redo captures the essential
simplicity and flexibility of make, while avoiding its flaws.  It manages to
do this while being simultaneously simpler than make, more flexible than
make, and more powerful than make, and without sacrificing performance - a
rare combination of features.

The original design for redo comes from Daniel J. Bernstein (creator of
qmail and djbdns, among many other useful things).  He posted some
terse notes on his web site at one point (there is no date) with the
unassuming title, "[Rebuilding target files when source files have
changed](http://cr.yp.to/redo.html)." Those notes are enough information to
understand how the system is supposed to work; unfortunately there's no code
to go with it.  I wrote this implementation of redo from scratch, based on
that design.

After I found out about djb redo, I searched the Internet for any sign that
other people had discovered what I had: a hidden, unimplemented gem of
brilliant code design.  I found only one interesting link at the time: Alan
Grosskurth, whose [Master's thesis at the University of
Waterloo](http://grosskurth.ca/papers/mmath-thesis.pdf) was about top-down
software rebuilding, that is, djb redo.  He wrote his own (admittedly slow)
implementation in about 250 lines of shell script, which gives an idea for
how straightforward the system is.  Since then, several other
implementations have appeared (see list below).

My implementation of redo is called `redo` for the same reason that there
are 75 different versions of `make` that are all called `make`.  It's somehow
easier that way.

I also provide an extremely minimal pure-POSIX-sh implementation, called
`do`, in the `minimal/` directory of this repository.

(Want to discuss redo?  Join [our mailing list](Contributing/#mailing-list).)


# What's so special about redo?

The theory behind redo sounds too good to be true: it can do everything
`make` can do, but the implementation is vastly simpler, the syntax is
cleaner, and you have even more flexibility without resorting to ugly hacks. 
Also, you get all the speed of non-recursive `make` (only check dependencies
once per run) combined with all the cleanliness of recursive `make` (you
don't have code from one module stomping on code from another module).

(Disclaimer: my current implementation is not as fast as `make` for some
things, because it's written in python.  Eventually I'll rewrite it in C and
it'll be very, very fast.)

The easiest way to show it is to jump into an example.  Here's one for
compiling a C++ program.

Create a file called default.o.do:

	redo-ifchange $2.c
	gcc -MD -MF $2.d -c -o $3 $2.c
	read DEPS <$2.d
	redo-ifchange ${DEPS#*:}

Create a file called myprog.do:

	DEPS="a.o b.o"
	redo-ifchange $DEPS
	gcc -o $3 $DEPS
	
Of course, you'll also have to create `a.c` and `b.c`, the C language
source files that you want to build to create your application.

In a.c:

	#include <stdio.h>
	#include "b.h"
	
	int main() { printf(bstr); }
	
In b.h:

	extern char *bstr;
	
In b.c:

	char *bstr = "hello, world!\n";

Now you simply run:

	$ redo myprog
	
And it says:

	redo  myprog
	redo    a.o
	redo    b.o

Now try this:

	$ touch b.h
	$ redo myprog
	
Sure enough, it says:

	redo  myprog
	redo    a.o

Did you catch the shell incantation in `default.o.do` where it generates
the autodependencies?  The filename `default.o.do` means "run this script to
generate a .o file unless there's a more specific whatever.o.do script that
applies."

The key thing to understand about redo is that declaring a dependency is just
another shell command.  The `redo-ifchange` command means, "build each of my
arguments.  If any of them or their dependencies ever change, then I need to
run the *current script* over again."

Dependencies are tracked in a persistent `.redo` database so that redo can
check them later.  If a file needs to be rebuilt, it re-executes the
`whatever.do` script and regenerates the dependencies.  If a file doesn't
need to be rebuilt, redo figures that out just using its persistent
`.redo` database, without re-running the script.  And it can do that check
just once right at the start of your project build, which is really fast.

Best of all, as you can see in `default.o.do`, you can declare a dependency
*after* building the program.  In C, you get your best dependency
information by trying to actually build, since that's how you find out which
headers you need.  redo is based on this simple insight: you don't
actually care what the dependencies are *before* you build the target.  If
the target doesn't exist, you obviously need to build it.

Once you're building it anyway, the build script itself can calculate the
dependency information however it wants; unlike in `make`, you don't need a
special dependency syntax at all.  You can even declare some of your
dependencies after building, which makes C-style autodependencies much
simpler.

redo therefore is a unique combination of imperative and declarative
programming.  The initial build is almost entirely imperative (running a
series of scripts).  As part of that, the scripts declare dependencies a few
at a time, and redo assembles those into a larger data structure.  Then, in
the future, it uses that pre-declared data structure to decide what work
needs to be redone.

(GNU make supports putting some of your dependencies in include files, and
auto-reloading those include files if they change.  But this is very
confusing - the program flow through a Makefile is hard to trace already,
and even harder when it restarts from the beginning because an include file
changes at runtime.  With redo, you can just read each build script from top
to bottom.  A `redo-ifchange` call is like calling a function, which you can
also read from top to bottom.)


# What projects use redo?

Some larger proprietary projects are using it, but unfortunately they can't
easily be linked from this document.  Here are a few open source examples:

* [Liberation Circuit](https://github.com/linleyh/liberation-circuit) is a
  straightforward example of a C++ binary (a game) compiled with redo.

* [WvStreams](https://github.com/apenwarr/wvstreams) uses a more complex
  setup producing several binaries, libraries, and scripts.  It shows how to
  produce output files in a different directory than the source files.

* [WvBuild](https://github.com/apenwarr/wvbuild) can cross-compile several
  dependencies, like openssl and zlib, and then builds WvStreams using those
  same libraries.  It's a good example of redo/make interop and complex
  dependencies.

* There's an experimental [variant of
  Buildroot](https://github.com/apenwarr/buildroot/tree/redo) that uses redo
  in order to clean up its dependency logic.

* You can find some curated tutorial examples in the
  [cookbook](cookbook/hello/), such as [git variable
  substitution](cookbook/defaults/) and [text processing with
  LaTeX](cookbook/latex/) (including plot generation with R and ggplot2).

* A [github search for all.do](https://github.com/search?p=9&q=path%3A%2F+extension%3Ado+filename%3A%2Fall.do&type=Code)
  shows an ever-growing number of projects using redo.

If you switch your program's build process to use redo, please let us know and
we can link to it here for some free publicity.

(Please don't use the integration testing code in the redo project's `t/`
directory as serious examples of how to use redo.  Many of the tests are
doing things in intentionally psychotic ways in order to stress redo's code
and find bugs.  On the other hand, if you're building your own
reimplementation of redo, using our test suite is a great idea.)


# How does this redo compare to other redo implementations?

djb never released his version, so other people have implemented their own
variants based on his [published specification](http://cr.yp.to/redo.html).

This version, sometimes called apenwarr/redo, is probably the most advanced
one, including support for parallel builds,
[resilient timestamps](https://apenwarr.ca/log/20181113) and checksums,
[build log linearization](https://apenwarr.ca/log/20181106), and
helpful debugging features.  It's currently written in python for easier
experimentation, but the plan is to eventually migrate it to plain C.  (Some
people like to call this version "python-redo", but I don't like that name. 
We shouldn't have to rename it when we later transliterate the code to C.)

Here are some other redo variants (thanks to Nils Dagsson Moskopp for
collecting many of these links):

- Alan Grosskurth's [redo thesis](http://grosskurth.ca/papers/mmath-thesis.pdf)
  and related sh implementation.  (Arguably, this paper is the one that got
  all the rest of us started.)

- Nils Dagsson Moskopp's [redo-sh](https://web.archive.org/web/20181106195145/http://news.dieweltistgarnichtso.net/bin/redo-sh.html)
  is a completely self-sufficient sh-based implementation.

- apenwarr's [minimal/do](https://github.com/apenwarr/redo/blob/master/minimal/do)
  is included with this copy of redo.  It's also sh-based, but intended to
  be simple and failsafe, so it doesn't understand how to "redo" targets more
  than once.

- Christian Neukirchen's [redo-c](https://github.com/chneukirchen/redo-c), a
  C implementation.

- Jonathan de Boyne Pollard's [fork of Alan Grosskurth's redo](http://jdebp.eu./Softwares/redo/grosskurth-redo.html)
  (another sh-based implementation).

- Jonathan de Boyne Pollard's [redo](http://jdebp.eu./Softwares/redo/)
  rewritten in C++

- Gyepi Sam's [redux](https://github.com/gyepisam/redux) in Go

- jekor's [redo](https://github.com/jekor/redo) in Haskell

- Shanti Bouchez-Mongardé (mildred)'s [fork of apenwarr's redo](https://github.com/mildred/redo)
  in python

- Tharre's [redo](https://github.com/Tharre/redo) in C

- catenate's [credo](https://github.com/catenate/credo), a (very
  rearchitected) variant written for the Inferno Shell.

The original redo design is so simple and elegant that many individuals
have been
inspired to (and able to) write their own version of it.  In the honoured
tradition of Unix's `make`, they (almost) all just use the same name,
`redo`.  Unfortunately, many of these
implementations are unmaintained, slightly incompatible with the "standard"
redo semantics, and/or have few or no automated tests.

At the time of this writing, none of them except apenwarr/redo (ie.  this
project) correctly support parallel builds (`redo -j`) or log linearization
(`redo-log`).  For large projects, parallel builds are usually considered
essential.

The [automated tests](https://github.com/apenwarr/redo/tree/master/t) in
this version of redo are almost, but not quite, appropriate for testing any
redo implementation.  If you really must write a new version of redo, we
invite you to thoroughly test it against the existing test suite to ensure
compatibility.  You can also steal our tests (with attribution, of course)
and include them in your own source package.  We'd also love it if you
contribute more automated tests when you find a bug, or send us patches if
you find a test which is accidentally incompatible (as opposed to finding a
real bug) with other redo implementations.
