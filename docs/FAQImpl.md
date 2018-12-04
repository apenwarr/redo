# Does redo run on Windows?

redo works fine in [Windows Services for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/initialize-distro)
on Windows 10.  You might consider that to be "real" Windows, or not.  If
you use it, it runs more or less like it does on Linux.  WSL is considerably
slower than native Linux, so there is definitely room for speed improvements.

If I were going to port redo to Windows in a "native" way,
I might grab the source code to a posix shell (like the
one in MSYS) and link it directly into redo.

One interesting project that has appeared recently is
busybox-w32 (https://github.com/pclouds/busybox-w32).  It's
a port of busybox to win32 that includes a mostly POSIX
shell (ash) and a bunch of standard Unix utilities.  This
might be enough to get your redo scripts working on a win32
platform without having to install a bunch of stuff.  But
all of this needs more experimentation.


# Can a *.do file itself be generated as part of the build process?

Yes and no.  Kind of.  Redo doesn't stop you from doing this, and it will
use a .do file if you generate one.  However, you have to do the steps in
the right order if you want this to work.  For example, this should work
fine:

	redo-ifchange default.o.do
	redo-ifchange foo.o

You've told redo to generate `default.o.do` (presumably using a
script like default.do.do), and *then* you've told redo to generate `foo.o`. 
When it considers how to build `foo.o`, it will look for a .do file, and
thus find `default.o.do`, so it'll run it.  Great.

Some people would like us to go a step further, and *automatically* look for
rules that will help produce default.o.do.  That is, you might want to just
write this:

	redo-ifchange foo.o bar.o

and then expect that, implicitly, redo will know it needs to look for
`default.o.do`, and if `default.o.do` doesn't exist yet, it should look for
`default.do.do`, and so on.

The problem with this idea is...  where does it end?  If there's no
`default.o.do`, so we look for a `default.do.do`, what if that doesn't exist
either?  Perhaps there's a `default.do.do.do` for generating `default.do.do`
files?  And so on.  You'd have to draw an arbitrary line somewhere.

Anyway, unlike make, redo does *not* implicitly generate files.
It only generates a given file if you redo-ifchange that file
first, from one of your other .do scripts.  This gets avoids magical
behaviour, but makes it quite tricky to auto-generate .do files.  See the
next question for a workaround.


# What can I do instead of auto-generating *.do files?

When people ask about auto-generating .do files, they usually mean one of
two things:

1. They want to create a new directory and auto-populate it with .do files
copied from somewhere.

    - This can be solved in various ways.  For example, you might make a
      trivial toplevel `default.do` file in the new directory; this will
      match all possible targets.  You can then use the sh "source" operator
      (.) and `redo-whichdo` to pull the "real" rules from elsewhere.  An
      example of [.do file delegation can be found in the wvstreams
      project](https://github.com/apenwarr/wvstreams/blob/master/delegate.od).

2. They want to generate, eg. `default.o.do` based on auto-detected compiler
settings, in order to support different brands of compilers, or different
architectures, etc.

    - The trick here is not to generate `default.o.do`, but rather to
      generate another script instead.  For example, you could have a
      `compile.do` that generates a script called `compile`.  `default.o.do`
      would simply be hard coded to something like `./compile $2 $3`.  The
      wvstreams project also has [an example of
      compile.do](https://github.com/apenwarr/wvstreams/blob/master/compile.do).

    - The advantage of separating out into separate default.o.do and compile
      scripts is that you can put all your system-dependent conditionals
      into compile.do, so they run only once and choose the "right" compile
      command.  Then, for each file, you can simply run that command.  If
      This kind of micro-optimization doesn't appeal to you, then there's no
      shame in just putting all the logic directly into `default.o.do`.


# How does redo store dependencies?

At the toplevel of your project, redo creates a directory
named `.redo`.  That directory contains a sqlite3 database
with dependency information.

The format of the `.redo` directory is undocumented because
it may change at any time.  It will likely turn out that we
can do something simpler than sqlite3.  If you really need to make a
tool that pokes around in there, please ask on the mailing
list if we can standardize something for you.

Unfortunately, the design of having a *single* .redo directory at the
toplevel of a project has proven problematic: what exactly is the "top
level" of a "project"?  If your project is a subdirectory of another project
that then switches to redo, should the .redo directory move up a level in
the hierarchy when that happens?  And so on.  Eventually, we will
probably migrate to a system where there is one .redo directory per target
directory.  This avoids all kinds of problems with symlinks, directory
renames nested projects, and so on.

# Isn't using sqlite3 overkill?  And un-djb-ish?

Well, yes.  Sort of.  I think people underestimate how
"lite" sqlite really is:

	root root 573376 2010-10-20 09:55 /usr/lib/libsqlite3.so.0.8.6

573k for a *complete* and *very fast* and *transactional*
SQL database.  For comparison, libdb is:

	root root 1256548 2008-09-13 03:23 /usr/lib/libdb-4.6.so

...more than twice as big, and it doesn't even have an SQL parser in
it!  Or if you want to be really horrified:

	root root 1995612 2009-02-03 13:54 /usr/lib/libmysqlclient.so.15.0.0

The mysql *client* library is two megs, and it doesn't even
have a database in it!  People who think SQL
databases are automatically bloated and gross have not yet
actually experienced the joys of sqlite.  SQL has a
well-deserved bad reputation, but sqlite is another story
entirely.  It's excellent, and much simpler and better
written than you'd expect.

Still, it's not very "djbish" to use a
general-purpose database, especially one that has a *SQL
parser* in it.  (One of the great things about redo's
design is that it doesn't ever need to parse anything, so
embedding a whole SQL parser is a bit embarrassing.)

I'm pretty sure djb never would have done it that way.
However, I don't think we can reach the performance we want
with dependency/build/lock information stored in plain text
files; among other things, that results in too much
fstat/open activity, which is slow in general, and even
slower if you want to run on Windows.  That leads us to a
binary database.  And example of the kind of structure we need is the [one
used by ninja](https://github.com/ninja-build/ninja/blob/master/src/deps_log.h#L29)
which is very simple, fast, and efficient.

Most of the state database stuff has been isolated in
state.py.  If you're feeling brave, you can try to
implement your own better state database, with or without
sqlite.


# What hash algorithm does redo-stamp use?

It's intentionally undocumented because you shouldn't need
to care and it might change at any time.  But trust me,
it's not the slow part of your build, and you'll never
accidentally get a hash collision.


# Why not *always* use checksum-based dependencies instead of timestamps?

Some build systems keep a checksum of target files and rebuild dependents
only when the target changes.  This is appealing in some cases; for example,
with ./configure generating config.h, it could just go ahead and generate
config.h; the build system would be smart enough to rebuild or not rebuild
dependencies automatically.  This keeps build scripts simple and gets rid of
the need for people to re-implement file comparison over and over in every
project or for multiple files in the same project.

There are disadvantages to using checksums for everything
automatically, however:

- Building stuff unnecessarily is *much* less dangerous
  than not building stuff that should be built.  Checksums
  aren't perfect (think of zero-byte output files); using
  checksums will cause more builds to be skipped by
  default, which is very dangerous.

- It makes it hard to *force* things to rebuild when you
  know you absolutely want that.  (With timestamps, you can
  just `touch filename` to rebuild everything that depends
  on `filename`.)

- Targets that are just used for aggregation (ie. they
  don't produce any output of their own) would always have
  the same checksum - the checksum of a zero-byte file -
  which causes confusing results.

- Calculating checksums for every output file adds time to
  the build, even if you don't need that feature.

- Building stuff unnecessarily and then stamping it is
  much slower than just not building it in the first place,
  so for *almost* every use of redo-stamp, it's not the
  right solution anyway.

- To steal a line from the Zen of Python: explicit is
  better than implicit.  Making people think about when
  they're using the stamp feature - knowing that it's slow
  and a little annoying to do - will help people design
  better build scripts that depend on this feature as
  little as possible.

- djb's (as yet unreleased) version of redo doesn't
  implement checksums, so doing that would produce an
  incompatible implementation.  With redo-stamp and
  redo-always being separate programs, you can simply
  choose not to use them if you want to keep maximum
  compatibility for the future.

- Bonus: the redo-stamp algorithm is interchangeable.  You
  don't have to stamp the target file or the source files
  or anything in particular; you can stamp any data you
  want, including the output of `ls` or the content of a
  web page.  We could never have made things like that
  implicit anyway, so some form of explicit redo-stamp
  would always have been needed, and then we'd have to
  explain when to use the explicit one and when to use the
  implicit one.

Thus, we made the decision to only use checksums for
targets that explicitly call `redo-stamp` (see previous
question).

I suggest actually trying it out to see how it feels for
you.  For myself, before there was redo-stamp and
redo-always, a few types of problems (in particular,
depending on a list of which files exist and which don't)
were really annoying, and I definitely felt it.  Adding
redo-stamp and redo-always work the way they do made the
pain disappear, so I stopped changing things.

A longer and even more detailed explanation of timestamp vs checksum-based
build dependencies can be found in
[mtime comparison considered harmful](https://apenwarr.ca/log/20181113).


# Why doesn't redo by default print the commands as they are run?

make prints the commands it runs as it runs them.  redo doesn't, although
you can get this behaviour with `redo -v` or `redo -x`. 
(The difference between -v and -x is the same as it is in
sh... because we simply forward those options onward to sh
as it runs your .do script.)

The main reason we don't do this by default is that the commands get
pretty long
winded (a compiler command line might be multiple lines of repeated
gibberish) and, on large projects, it's hard to actually see the progress of
the overall build.  Thus, make users often work hard to have make hide the
command output in order to make the log "more readable."

The reduced output is a pain with make, however, because if there's ever a
problem, you're left wondering exactly what commands were run at what time,
and you often have to go editing the Makefile in order to figure it out.

With redo, it's much less of a problem.  By default, redo produces output
that looks like this:

	$ redo t
	redo  t/all
	redo    t/hello
	redo      t/LD
	redo      t/hello.o
	redo        t/CC
	redo    t/yellow
	redo      t/yellow.o
	redo    t/bellow
	redo    t/c
	redo      t/c.c
	redo        t/c.c.c
	redo          t/c.c.c.b
	redo            t/c.c.c.b.b
	redo    t/d

The indentation indicates the level of recursion (deeper levels are
dependencies of earlier levels).  The repeated word "redo" down the left
column looks strange, but it's there for a reason, and the reason is this:
you can cut-and-paste a line from the build script and rerun it directly.

	$ redo t/c
	redo  t/c
	redo    t/c.c
	redo      t/c.c.c
	redo        t/c.c.c.b
	redo          t/c.c.c.b.b

So if you ever want to debug what happened at a particular step, you can
choose to run only that step in verbose mode:

	$ redo t/c.c.c.b.b -x
	redo  t/c.c.c.b.b
	* sh -ex default.b.do c.c.c.b .b c.c.c.b.b.redo2.tmp
	+ redo-ifchange c.c.c.b.b.a
	+ echo a-to-b
	+ cat c.c.c.b.b.a
	+ ./sleep 1.1
	redo  t/c.c.c.b.b (done)

If you're using an autobuilder or something that logs build results for
future examination, you should probably set it to always run redo with
the -x option.


# How fast is redo compared to make?

FIXME:
The current version of redo is written in python and has not been optimized. 
So right now, it's usually a bit slower.  Not too embarrassingly slower,
though, and the slowness mostly only strikes when you're
building a project from scratch.

For incrementally building only the changed parts of the project, redo can
be much faster than make, because it can check all the dependencies up
front and doesn't need to repeatedly parse and re-parse the Makefile (as
recursive make needs to do).

redo's sqlite3-based dependency database is very fast (and
it would be even faster if we rewrite redo in C instead of
python).  Better still, it would be possible to write an
inotify daemon that can update the dependency database in
real time; if you're running the daemon, you can run 'redo'
from the toplevel and if your build is clean, it could return
instantly, no matter how many dependencies you have.

On my machine, redo can currently check about 10,000
dependencies per second.  As an example, a program that
depends on every single .c or .h file in the Linux kernel
2.6.36 repo (about 36000 files) can be checked in about 4
seconds.

Rewritten in C, dependency checking would probably go about
10 times faster still.

This probably isn't too hard; the design of redo is so simple that
it should be easy to write in any language.  It's just
*even easier* in python, which was good for writing the
prototype and debugging the parallelism and locking rules.

Most of the slowness at the moment is because redo-ifchange
(and also sh itself) need to be fork'd and exec'd over and
over during the build process.

As a point of reference, on my computer, I can fork-exec
redo-ifchange.py about 87 times per second; an empty python
program, about 100 times per second; an empty C program,
about 1000 times per second; an empty make, about 300 times
per second.  So if I could compile 87 files per second with
gcc, which I can't because gcc is slower than that, then
python overhead would be 50%.  Since gcc is slower than
that, python overhead is generally much less - more like
10%.

Also, if you're using redo -j on a multicore machine, all
the python forking happens in parallel with everything
else, so that's 87 per second per core.  Nevertheless,
that's still slower than make and should be fixed.

(On the other hand, all this measurement is confounded
because redo's more fine-grained dependencies mean you can
have more parallelism.  So if you have a lot of CPU cores, redo
might build *faster* than make just because it makes better
use of them.)
