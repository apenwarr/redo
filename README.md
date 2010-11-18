# redo: a top-down software build system

`redo` is a competitor to the long-lived, but sadly imperfect, `make`
program.  There are many such competitors, because many people over the
years have been dissatisfied with make's limitations.  However, of all the
replacements I've seen, only redo captures the essential simplicity and
flexibility of make, while eliminating its flaws.  To my great surprise, it
manages to do this while being simultaneously simpler than make, more
flexible than make, and more powerful than make.

Although I wrote redo and I would love to take credit for it, this magical
simplicity and flexibility comes because I copied verbatim a design by
Daniel J. Bernstein (creator of qmail and djbdns, among many other useful
things).  He posted some very terse notes on his web site at one point
(there is no date) with the unassuming title, "[Rebuilding target files when
source files have changed](http://cr.yp.to/redo.html)." Those notes are
enough information to understand how the system it supposed to work;
unfortunately there's no code to go with it.  I get the impression that the
hypothetical "djb redo" is incomplete and Bernstein doesn't yet consider it
ready for the real world.

I was led to that particular page by random chance from a link on [The djb
way](http://thedjbway.b0llix.net/future.html), by Wayne Marshall.

After I found out about djb redo, I searched the Internet for any sign that
other people had discovered what I had: a hidden, unimplemented gem of
brilliant code design.  I found only one interesting link: Alan Grosskurth, whose
[Master's thesis at the University of
Waterloo](http://grosskurth.ca/papers/mmath-thesis.pdf) was about top-down
software rebuilding, that is, djb redo.  He wrote his own (admittedly slow)
implementation in about 250 lines of shell script.

If you've ever thought about rewriting GNU make from scratch, the idea of
doing it in 250 lines of shell script probably didn't occur to you.  redo is
so simple that it's actually possible.  For testing, I actually wrote an
even more minimal version (which always rebuilds everything instead of
checking dependencies) in only 70 lines of shell.

The design is simply that good.

This implementation of redo is called `redo` for the same reason that there
are 75 different versions of `make` that are all called `make`.  It's just
easier that way.  Hopefully it will turn out to be compatible with the other
implementations, should there be any.


# License

My version of redo was written without ever seeing redo code by Bernstein or
Grosskurth, so I own the entire copyright.  It's distributed under the GNU
LGPL version 2.  You can find a copy of it in the file called LICENSE.


# What's so special about redo?

The theory behind redo is almost magical: it can do everything `make` can
do, only the implementation is vastly simpler, the syntax is cleaner, and you
can do even more flexible things without resorting to ugly hacks.  Also, you
get all the speed of non-recursive `make` (only check dependencies once per
run) combined with all the cleanliness of recursive `make` (you don't have
code from one module stomping on code from another module).

But the easiest way to show it is with an example.

Create a file called default.o.do:
	redo-ifchange $1.c
	gcc -MD -MF $3.deps.tmp -c -o $3 $1.c
	DEPS=$(sed -e "s/^$3://" -e 's/\\//g' <$3.deps.tmp)
	rm -f $3.deps.tmp
	redo-ifchange $DEPS

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

The amazing innovation in redo - and really, this is the key innovation that
makes everything else work - is that declaring a dependency is just another
shell command.  The `redo-ifchange` command means, "build each of my
arguments.  If any of them or their dependencies ever change, then I need to
run the *current script* over again."

Dependencies are tracked in a persistent `.redo` database so that redo can
check them later.  If a file needs to be rebuilt, it re-executes the
`whatever.do` script and regenerates the dependencies.  If a file doesn't
need to be rebuilt, redo can calculate that just using its persistent
`.redo` database, without re-running the script.  And it can do that check
just once right at the start of your project build.

But best of all, as you can see in `default.o.do`, you can declare a
dependency *after* building the program.  In C, you get your best dependency
information by trying to actually build, since that's how you find out which
headers you need.  redo offers the following simple insight: you don't actually
care what the dependencies are *before* you build the file; if the file
doesn't exist, you obviously need to build it.  Then, the build script
itself can provide the dependency information however it wants; unlike in
`make`, you don't need a special dependency syntax at all.  You can even
declare your dependencies after building, which makes everything much
simpler.

(GNU make supports putting some of your dependencies in include files, and
auto-reloading those include files if they change.  But this is very
confusing - the program flow through a Makefile is hard to trace already,
and even harder if it restarts randomly from the beginning when a file
changes.  With redo, you can just read the script from top to bottom.  A
`redo-ifchange` call is like calling a function, which you can also read
from top to bottom.)

# One script per file?  Can't I just put it all in one big Redofile like make does?

One of my favourite features of redo is that it doesn't add any new syntax;
the syntax of redo is *just* the syntax of sh.

Also, it's surprisingly useful to have each build script in its own file;
that way, you can declare a dependency on just that one build script instead
of the entire Makefile, and you won't have to rebuild everything just
because of a one-line Makefile change.  (Some build tools avoid that
by tracking exactly which variables and commands were used to do the build. 
But that's more complex, more error prone, and slower.)

Still, it would be rather easy to make a "Redofile" parser that just has a
bunch of sections like this:

	myprog:
		DEPS="a.o b.o"
	        redo-ifchange $DEPS
                gcc -o $3 $DEPS

We could just auto-extract myprog.do by slurping out the indented sections
into their own files.  You could even write a .do file to do it.

It's not obvious that this would be a real improvement however.

See djb's [Target files depend on build
scripts](http://cr.yp.to/redo/honest-script.html) article for more
information.


# Can a *.do file itself be generated as part of the build process?

Not currently.  There's nothing fundamentally preventing us from allowing
it.  However, it seems easier to reason about your build process if you
*aren't* auto-generating your build scripts on the fly.

This might change.


# Do end users have to have redo installed in order to build my project?

No.  We include a very short (70 lines, as of this writing) shell script
called `do` in the `minimal` subdirectory of the redo project.  `do` is like
`redo` (and it works with the same `*.do` scripts), except it doesn't
understand dependencies; it just always rebuilds everything from the top.

You can include `do` with your program to make it so non-users of redo can
still build your program.  Someone who wants to hack on your program will
probably go crazy unless they have a copy of `redo` though.

Actually, `redo` itself isn't so big, so for large projects where it
matters, you could just include it with your project.


# How does redo store dependencies?

FIXME:
Currently, in a directory called `.redo` that's full of text files.  This
isn't really optimal, so it will change eventually.  Please consider the
storage format undocumented (but feel free to poke around and look; it's
simple enough).


# If a target didn't change, how to I prevent dependents from being rebuilt?

For example, running ./configure creates a bunch of files including
config.h, and config.h might or might not change from one run to the next. 
We don't want to rebuild everything that depends on config.h if config.h is
identical.

With `make`, which makes build decisions based on timestamps, you would
simply have the ./configure script write to config.h.new, then only
overwrite config.h with that if the two files are different.

FIXME:
This is not possible in the current version of `redo`.  redo knows whenever it
rebuilds a target and doesn't bother re-checking dependencies after that;
even if the file didn't technically change, it is considered "rebuilt,"
which means all its dependants now need to be rebuilt.

The advantage of this method is you can't accidentally prevent the
rebuilding of things just by marking the target files as "newer" or marking
the source files as "older" (as sometimes happens when you extract an old
tarball or backup on top of your source code files).  The disadvantage is
unnecessary rebuilding of some stuff sometimes.

We will have to find a solution to this before redo 1.0.

See also the next question.


# What about checksum-based dependencies instead of timestamp-based ones?

Some build systems keep a checksum of target files and rebuild dependants
only when the target changes.  This is appealing in some cases; for example,
with ./configure generating config.h, it could just go ahead and generate
config.h; the build system would be smart enough to rebuild or not rebuild
dependencies automatically.  This keeps build scripts simple and gets rid of
the need for people to re-implement file comparison over and over in every
project or for multiple files in the same project.

I think this would be a good addition to `redo` - and not a very difficult
one.

Probably we should add a new command similar to `redo-ifchange`; let's call
it `redo-ifsum` or `redo-ifdiff`.  That command would verify checksums
instead of timestamps.

Sometimes you don't want to use checksums for verification; for example, in
some complicated build systems, you want to create empty `something.stamp`
files to indicate that some big complex operation has completed
successfully.  But empty files all have the same checksum, so perhaps you'd
rather just use a timestamp comparison in that case.  (Alternatively, you
could fill the file with data - maybe a series of checksums - indicating the
state of the data that was produced.  If that data changed, the stamp would
then be out of date.)

FIXME: This requires a bit more thought before we commit to any particular
option.


# Can my .do files be written in a language other than sh?

FIXME: Not presently.  In theory, we could support starting your .do files
with the magic "#!/" sequence (eg. #!/usr/bin/python) and then using that
shell to run your .do script.  But that opens new problems, like figuring
out what is the equivalent of the `redo-ifchange` command in python.  Do you
just run it in a subprocess?  That might be unnecessarily slow.  And so on.

Right now, `redo` explicitly runs `sh -c filename.do`.  The main reasons for
this are to make the #!/ line optional, and so you don't have to remember to
`chmod +x` your .do files.


# Can a single .do script generate multiple outputs?

FIXME: Not presently.  This seems like a useful feature though.

For example, you could have a file called `default.do.do` that would
generate .do files from a `Redofile`.  Then you wouldn't have to argue with
the `redo` maintainers about whether putting stuff into a single `Redofile`
is better than the current behaviour.

Right now you could do that, except you would want to parse the `Redofile`
only once and produce a bunch of `.do` files from that single action.  But
you would still want `redo` to know which `.do` files were produced, so it
could rerun the splitter script, if `Redofile` ever changed, before using
one of the generated `.do` files.

It would also be useful, again, with ./configure: typically running the
configure script produces several output files, and it would be nice to
declare dependencies on all of them.


# Recursive make is considered harmful.  Isn't redo even *more* recursive?

You probably mean [this 1997 paper](http://miller.emu.id.au/pmiller/books/rmch/)
by Peter Miller.

Yes, redo is recursive, in the sense that every target is built by its own
`.do` file, and every `.do` file is a shell script being run recursively
from other shell scripts, which might call back into `redo`.  In fact, it's
even more recursive than recursive make.

However the reason recursive make is considered harmful is that each
instance of make has no access to the dependency information seen by the
other instances.  Each one starts from its own Makefile, which only has a
partial picture of what's going on; moreover, each one has to stat a lot of
the same files over again, leading to slowness.  That's the thesis of the
"considered harmful" paper.

On the other hand, nobody has written a paper about it, but non-recursive
make should also be considered harmful.  The problem is Makefiles aren't
very "hygienic" or "modular"; if you're not running make recursively, then
your one copy of make has to know *everything* about *everything* in your
entire project.  Every variable in make is global, so every variable defined
in *any* of your Makefiles is visible in *all* of your Makefiles.  Every
little private function or macro is visible everywhere.  In a huge project
made up of multiple projects from multiple vendors, that's just not okay.

`redo` deftly manages to dodge both sets of problems.  First of all,
dependency information is shared through a global persistent `.redo`
directory, which is accessed by all your `redo` instances at once. 
Dependencies created or checked by one instance can be immediately used by
another instance.  And there's locking to prevent two instances from
building the same target at the same time.  So you get all the "global
dependency" knowledge of non-recursive make.

But also, every `.do` script is entirely hygienic and traceable; `redo`
discourages the use of global environment variables, suggesting that you put
settings into files (which can have timestamps and dependencies) instead. 
So you also get all the hygiene and modularity advantages of recursive make.

By the way, you can trace any `redo` build process just by reading the `.do`
scripts from top to bottom.  Makefiles are actually a collection of "rules"
whose order of execution is unclear; any rule might run at any time.  In a
non-recursive Makefile setup with a bunch of included files, you end up with
lots and lots of rules that can all be executed in a random order; tracing
becomes impossible.  Recursive make tries to compensate for this by breaking
the rules into subsections, but that ends up with all the "considered harmful"
paper's complaints.  `redo` just runs from top to bottom in a nice tree, so
it's traceable no matter how many layers you have.

# How do I set environment variables that affect the entire build?

Directly using environment variables is a bad idea because you can't declare
dependencies on them.  Also, if there were a file that contained a set of
variables that all your .do scripts need to run, then `redo` would have to
read that file every time it starts (which is frequently, since it's
recursive), and that could get slow.

Luckily, there's an alternative.  Once you get used to it, this method is
actually much better than environment variables, because it runs faster
*and* it's easier to debug.

For example, djb often uses a computer-generated script called `compile` for
compiling a .c file into a .o file.  To generate the `compile` script, we
create a file called `compile.do`:
	
	redo-ifchange config.sh
	. ./config.sh
	echo "gcc -c -o \$3 $1.c $CFLAGS"
	chmod a+x $3

(Note that if a .do script produces data to stdout, like we have here, then
`redo` will use that to atomically update the target file.  So you don't
have to redirect it yourself, or worry about using a temp file and then
renaming it.)

Then, your `default.o.do` can simply look like this:

	redo-ifchange compile $1.c
	./compile $1 $2 $3

This is not only elegant, it's useful too.  With make, you have to always
output everything it does to stdout/stderr so you can try to figure out
exactly what it was running; because this gets noisy, some people write
Makefiles that deliberately hide the output and print something friendlier,
like "Compiling hello.c".  But then you have to guess what the compile
command looked like.

With redo, the command *is* `./compile hello.c`, which looks good when
printed, but is also completely meaningful.  Because it doesn't depend on
any environment variables, you can just run `./compile hello.c` to reproduce
its output, or you can look inside the `compile` file to see exactly what
command line is being used.

As a bonus, all the variable expansions only need to be done once: when
generating the ./compile program.  With make, it would be recalculating
expansions every time it compiles a file.

# How do I write a default.o.do that works for both C and C++ source?

See the previous answer for why you will probably use a compile.do instead. 
Then your default.o.do looks like it does in the previous answer.  We can
then upgrade compile.do to look something like this:

        redo-ifchange config.sh
        . ./config.sh
        cat <<-EOF
                [ -e "\$1.cc" ] && EXT=.cc || EXT=.c
                gcc -o "\$3" -c "\$1\$EXT" -Wall $CFLAGS
        EOF
        chmod a+x "$3"

Isn't it expensive to have ./compile doing this kind of test for every
single source file?  Not really.  Remember, if you have two implicit rules
in make:

	%.o: %.cc
		gcc ...

	%.o: %.c
		gcc ...
		
Then it has to do all the same checks.  Except make has even *more* implicit
rules than that, so it ends up trying and discarding lots of possibilities
before it actually builds your program.

So in this case, it's not implicit at all; you're specifying exactly how to
decide whether it's a C program or a C++ program, and what to do in each
case.  You can also share the two gcc command lines between the two rules,
which is hard in make.  (In GNU make you can use macro functions, but the
syntax for those is ugly.)

# Can I just rebuild a part of the project?

Absolutely!  Although `redo` runs "top down" in the sense of one .do file
calling into all its dependencies, you can start at any point in the
dependency tree that you want.

Unlike recursive make, no matter which subdir of your project you're in when
you start, `redo` will be able to build all the dependencies in the right
order.

Unlike non-recursive make, you don't have to jump through any strange hoops
(like adding a fake Makefile in each directory that does `make -C ${TOPDIR}`
back up to the main non-recursive Makefile).  redo just uses `filename.do`
to build `filename`, or uses `default*.do` if the specific `filename.do`
doesn't exist.

When running any .do file, `redo` makes sure its current directory is set to
the directory where the .do file is located.  That means you can do this:

	redo ../utils/foo.o
	
And it will work exactly like this:

	cd ../utils
	redo foo.o


# Can my filenames have spaces in them?

Yes, unlike with make.  For historical reasons, the Makefile syntax doesn't
support filenames with spaces; spaces are used to separate one filename from
the next, and there's no way to escape these spaces.

Since redo just uses sh, which has working escape characters and
quoting, it doesn't have this problem.


# Does redo care about the differences between tabs and spaces?

No.


# What if my .c file depends on a generated .h file?

This problem arises as follows.  foo.c includes config.h, and config.h is
created by running ./configure.  The second part is easy; just write a config.h.do
that depends on the existence of configure (which is created by
configure.do, which probably runs autoconf).

The first part, however, is not so easy.  Normally, the headers that a C
file depends on are detected as part of the compilation process.  That works
fine if the headers, themselves, don't need to be generated first.  But if
you do

	redo foo.o
	
There's no way for redo to know that compiling foo.c into foo.o depends on
first generating config.h.

FIXME:
There seem to be a few workarounds for this, but none are very good.  You
can explicitly make all .o files depend on config.h (which will cause things
to get recompiled unnecessarily).  You can just tell people to run
./configure before running redo (which is what make users typically do). 

You can try to guess dependencies using `gcc -MM -MG` (-MG means don't die
if headers aren't present), but that's not actually very helpful, because of
the compiler's header include paths: if I #include "foo.h", which directory
is redo supposed to look at to find foo.h?  All of them?  Normally a C
file's autodependencies have full paths attached, so this would be special.

[djb has a solution for his own
projects](http://cr.yp.to/redo/honest-nonfile.html), which is a simple
script that looks through C files to pull out #include lines.  He assumes
that `#include <file.h>` is a system header (thus not subject to being
built) and `#include "file.h"` is in the current directory (thus easy to
find).  Unfortunately this isn't really a complete solution in the general
case.

Maybe just telling redo to try to generate the file in all possible
locations is the best way to go.  But we need to think about this more.

In the meantime, you'll have to explicitly specify such dependencies in your
*.o.do files.


# Why don't you by default print the commands as they are run?

make prints the commands it runs as it runs them.  redo doesn't, although
you can get this behaviour with `redo -v`.

The main reason we made this decision is that the commands get pretty long
winded (a compiler command line might be multiple lines of repeated
gibberish) and, on large projects, it's hard to actually see the progress of
the overall build.  Thus, make users often work hard to have make hide the
command output in order to make the log "more useful."

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

	$ ./redo  t/c.c.c.b.b -v
	redo  t/c.c.c.b.b
	redo-ifchange "$1$2.a"
	echo a-to-b
	cat "$1$2.a"

If you're using an autobuilder or something that logs build results for
future examination, you should probably set it to always run redo with
the -v option.


# Is redo compatible with autoconf?

Yes.  You don't have to do anything special, other than the above note about
declaring dependencies on config.h, which is no worse than what you would
have to do with make.


# Is redo compatible with automake?

Hells no.  You can thank me later.  But see next question.


# Is redo compatible with make?

Yes.  If you have an existing Makefile (for example, in one of your
subprojects), you can just call make to build that subproject.

In a file called myproject.stamp.do:

	redo-ifchange $(find myproject -name '*.[ch]')
	make -C myproject all

So, to amend our answer to the previous question, you can include
automake-generated Makefiles as part of your redo-based project.


# Is redo -j compatible with make -j?

Yes!  redo implements the same jobserver protocol as GNU make, which means
that redo running under make -j, or make running under redo -j, will do the
right thing.  Thus, it's safe to mix-and-match redo and make in a recursive
build system.  Just make sure you declare your dependencies correctly.


# What about distributed builds?

FIXME:
So far, nobody has tried redo in a distributed build environment.  It surely
works with distcc, since that's just a distributed compiler.  But there are
other systems that distribute more of the build process to other machines.

The most interesting method I've heard of was explained (in public, this is
not proprietary information) by someone from Google.  Apparently, the
Android team uses a tool that mounts your entire local filesystem on a
remote machine using FUSE and chroots into that directory.  Then you replace
the $SHELL variable in your copy of make with one that runs this tool. 
Because the remote filesystem is identical to yours, the build will
certainly complete successfully.  After the $SHELL program exits, the changed
files are sent back to your local machine.  Cleverly, the files on the
remote server are cached based on their checksums, so files only need to be
re-sent if they have changed since last time.  This dramatically reduces
bandwidth usage compared to, say, distcc (which mostly just re-sends the
same preparsed headers over and over again).

At the time, he promised to open source this tool eventually.  It would be
pretty fun to play with it.

FIXME: However, it won't work as easily with redo as it did with make.  With
make, a separate copy of $SHELL is launched for each step of the build (and
gets migrated to the remote machine), but make runs only on your local
machine, so it can control parallelism and avoid building the same target
from multiple machines, and so on.  With redo, since the entire script runs
inside the shell, we'd have to do the parallelism another way.


# How fast is redo compared to make?

FIXME:
The current version of redo is written in python and has not been optimized. 
So right now, it's usually a bit slower.  Not too embarrassingly slower,
though, and the slowness really only strikes the first time you build a
project.

For incrementally building only the changed parts of the project, redo can
be much faster than make, because it can check all the dependencies up
front and doesn't need to repeatedly parse and re-parse the Makefile (as
recursive make needs to do).

More bad news, however: the current version of redo also pointlessly
re-evaluates the same dependencies over and over.  Unlike with make, there
is no good reason for this, so it'll be fixed eventually.

Even better, in 'redo -j' mode, it sometimes rebuilds the
same dependency more than once.  Not at the same time, so
your build won't break, but it'll just be unnecessarily
slow.  Obviously this should be fixed.

Furthermore, redo's current dependency database (in the `.redo` directory)
is not very efficient, and thrashes a lot of filesystem metadata, which is
especially slow on some filesystems, notably ext3.  We'll want to improve that
by using a "real" data structure eventually.  With a "real" data structure,
a daemon, and inotify, you could actually get redo's dependency evaluation
to run instantly.  On very large projects with tens of thousands of files to
stat() before we can even start building, that could make a pretty big
difference.  With make, an inotify implementation would be pretty hard to
do (since just parsing the Makefiles of such a project is complicated, and
there's no guarantee the dependencies are the same as last time).  But with
the way redo works, this kind of optimization would be pretty easy.

We'll probably have to rewrite redo in C eventually to speed it up further. 
This won't be very hard; the design is so simple that it should be easy to
write in any language.  It's just *even easier* in python,
which was good for writing a prototype.

Most of the so-called slowness at the moment (it's really not that bad)
is because redo-ifchange (and also sh itself) need to be fork'd and
exec'd over and over during the build process.  The `minimal/do` script
shows a way around this; redo-ifchange could be a shell function
instead of a standalone program.  Eliminating the need for extra
fork/exec in the common case could actually get us much faster than
make even when doing an initial build; make executes $SHELL for every
command, but with redo, there is a shell running at all times anyway,
so if we're very careful we could optimize that out.

As a point of reference, on my computer, I can fork-exec
redo-ifchange.py about 87 times per second; an empty python program,
about 100 times per second; an empty C program, about 1000 times per
second; an empty make, about 300 times per second.  So if I could
compile 87 files per second, which I can't, then python overhead
would be 50%.  Also, if you're using redo -j on a multicore machine, all
the python forking happens in parallel with everything else, so that's
87 per second per core.  Nevertheless, that's still slower than make and
should be fixed.


# What's missing?  How can I help?

redo is thoroughly incomplete and probably has numerous bugs.  Just what you
always wanted in a build system, I know.

What's missing?  Search for the word FIXME in this document; anything with a
FIXME is something that is either not implemented, or which needs
discussion, feedback, or ideas.  Of course, there are surely other
undocumented things that need discussion or fixes too.

You should join the redo-list@googlegroups.com mailing list.

You can find the mailing list archives here:

	http://groups.google.com/group/redo-list

Yes, it might not look like it, but you can subscribe without having a
Google Account.  Just send a message here:

	redo-list+subscribe@googlegroups.com

Note the plus sign.

Have fun,

Avery
