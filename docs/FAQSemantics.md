# Can I put all my rules in one big Redofile like make does?

One of my favourite features of redo is that it doesn't add any new syntax;
the syntax of redo is *exactly* the syntax of sh... because sh is the program
interpreting your .do file.

Also, it's surprisingly useful to have each build script in its own file;
that way, you can declare a dependency on just that one build script instead
of the entire Makefile, and you won't have to rebuild everything just
because of a one-line Makefile change.  (Some build tools avoid that same
problem by tracking which variables and commands were used to do the build. 
But that's more complex, more error prone, and slower.)

See djb's [Target files depend on build scripts](http://cr.yp.to/redo/honest-script.html)
article for more information.

However, if you really want to, you can simply create a
default.do that looks something like this:

	case $1 in
		*.o) ...compile a .o file... ;;
		myprog)  ...link a program... ;;
		*) echo "no rule to build '$1'" >&2; exit 1 ;;
	esac
	
Basically, default.do is the equivalent of a central
Makefile in make.  As of recent versions of redo, you can
use either a single toplevel default.do (which catches
requests for files anywhere in the project that don't have
their own .do files) or one per directory, or any
combination of the above.  And you can put some of your
targets in default.do and some of them in their own files. 
Lay it out in whatever way makes sense to you.

One more thing: if you put all your build rules in a single
default.do, you'll soon discover that changing *anything*
in that default.do will cause all your targets to rebuilt -
because their .do file has changed.  This is technically
correct, but you might find it annoying.  To work around
it, try making your default.do look like this:

	. ./default.od

And then put the above case statement in default.od
instead.  Since you didn't `redo-ifchange default.od`,
changes to default.od won't cause everything to rebuild.


# What are the parameters ($1, $2, $3) to a .do file?

NOTE: These definitions have changed since the earliest
(pre-0.10) versions of redo.  The new definitions match
what djb's original redo implementation did.

$1 is the name of the target file.

$2 is the basename of the target, minus the extension, if
any.

$3 is the name of a temporary file that will be renamed to
the target filename atomically if your .do file returns a
zero (success) exit code.

In a file called `chicken.a.b.c.do` that builds a file called
`chicken.a.b.c`, $1 and $2 are `chicken.a.b.c`, and $3 is a
temporary name like `chicken.a.b.c.tmp`.  You might have expected
$2 to be just `chicken`, but that's not possible, because
redo doesn't know which portion of the filename is the
"extension."  Is it `.c`, `.b.c`, or `.a.b.c`?

.do files starting with `default.` are special; they can
build any target ending with the given extension.  So let's
say we have a file named `default.c.do` building a file
called `chicken.a.b.c`. $1 is `chicken.a.b.c`, $2 is `chicken.a.b`,
and $3 is a temporary name like `chicken.a.b.c.tmp`.

You should use $1 and $2 only in constructing input
filenames and dependencies; never modify the file named by
$1 in your script.  Only ever write to the file named by
$3.  That way redo can guarantee proper dependency
management and atomicity.  (For convenience, you can write
to stdout instead of $3 if you want.)

For example, you could compile a .c file into a .o file
like this, from a script named `default.o.do`:
	
	redo-ifchange $2.c
	gcc -o $3 -c $2.c


# Why not $FILE, $BASE, $OUT instead of $1, $2, $3?

That sounds tempting and easy, but one downside would be
lack of backward compatibility with djb's original redo
design.

Longer names aren't necessarily better.  Learning the
meanings of the three numbers doesn't take long, and over
time, those extra few keystrokes can add up.  And remember
that Makefiles and perl have had strange one-character
variable names for a long time.  It's not at all clear that
removing them is an improvement.


# What happens to stdin/stdout/stderr?

As with make, stdin is not redirected.  You're probably
better off not using it, though, because especially with
parallel builds, it might not do anything useful.  We might
change this behaviour someday since it's such a terrible
idea for .do scripts to read from stdin.

As with make, stderr is also not redirected.  You can use
it to print status messages as your build proceeds. 
(Eventually, we might want to capture stderr so it's easier
to look at the results of parallel builds, but this is
tricky to do in a user-friendly way.)

Redo treats stdout specially: it redirects it to point at
$3 (see previous question).  That is, if your .do file
writes to stdout, then the data it writes ends up in the
output file.  Thus, a really simple `chicken.do` file that
contains only this:

    echo hello world

will correctly, and atomically, generate an output file
named `chicken` only if the echo command succeeds.


# Isn't it confusing to capture stdout by default?

Yes, it is.  It's unlike what almost any other program
does, especially make, and it's very easy to make a
mistake.  For example, if you write in your script:

	echo "Hello world"
	
it will go to the target file rather than to the screen.

A more common mistake is to run a program that writes to
stdout by accident as it runs.  When you do that, you'll
produce your target on $3, but it might be intermingled
with junk you wrote to stdout.  redo is pretty good about
catching this mistake, and it'll print a message like this:

	redo  zot.do wrote to stdout *and* created $3.
	redo  ...you should write status messages to stderr, not stdout.
	redo  zot: exit code 207

Despite the disadvantages, though, automatically capturing
stdout does make certain kinds of .do scripts really
elegant.  The "simplest possible .do file" can be very
short.  For example, here's one that produces a sub-list
from a list:

	redo-ifchange filelist
	grep ^src/ filelist
	
redo's simplicity is an attempt to capture the "Zen of
Unix," which has a lot to do with concepts like pipelines
and stdout.  Why should every program have to implement its
own -o (output filename) option when the shell already has
a redirection operator?  Maybe if redo gets more popular,
more programs in the world will be able to be even simpler
than they are today.

By the way, if you're running some programs that might
misbehave and write garbage to stdout instead of stderr
(Informational/status messages always belong on stderr, not
stdout!  Fix your programs!), then just add this line to
the top of your .do script:

	exec >&2
	
That will redirect your stdout to stderr, so it works more
like you expect.


# Run redo-ifchange in a loop?

The obvious way to write a list of dependencies might be
something like this:

	for d in *.c; do
		redo-ifchange ${d%.c}.o
	done

But it turns out that's very non-optimal.  First of all, it
forces all your dependencies to be built in order
(redo-ifchange doesn't return until it has finished
building), which makes -j parallelism a lot less useful. 
And secondly, it forks and execs redo-ifchange over and
over, which can waste CPU time unnecessarily.

A better way is something like this:

	for d in *.c; do
		echo ${d%.c}.o
	done |
	xargs redo-ifchange
	
That only runs redo-ifchange once (or maybe a few times, if
there are really a *lot* of dependencies and xargs has to
split it up), which saves fork/exec time and allows for
parallelism.


# If a target is identical after rebuilding, how do I prevent dependents from being rebuilt?

For example, running ./configure creates a bunch of files including
config.h, and config.h might or might not change from one run to the next. 
We don't want to rebuild everything that depends on config.h if config.h is
identical.

With `make`, which makes build decisions based on timestamps, you would
simply have the ./configure script write to config.h.new, then only
overwrite config.h with that if the two files are different. 
However, that's a bit tedious.

With `redo`, there's an easier way.  You can have a
config.do script that looks like this:

	redo-ifchange autogen.sh *.ac
	./autogen.sh
	./configure
	cat config.h configure Makefile | redo-stamp
	
Now any of your other .do files can depend on a target called
`config`.  `config` gets rebuilt automatically if any of
your autoconf input files are changed (or if someone does
`redo config` to force it).  But because of the call to
redo-stamp, `config` is only considered to have changed if
the contents of config.h, configure, or Makefile are
different than they were before.

(Note that you might actually want to break this .do up into a
few phases: for example, one that runs aclocal, one that
runs autoconf, and one that runs ./configure.  That way
your build can always do the minimum amount of work
necessary.)


# Why does 'redo target' redo even unchanged targets?

When you run `make target`, make first checks the
dependencies of target; if they've changed, then it
rebuilds target.  Otherwise it does nothing.

redo is a little different.  It splits the build into two
steps.  `redo target` is the second step; if you run that
at the command line, it just runs the .do file, whether it
needs it or not.

If you really want to only rebuild targets that have
changed, you can run `redo-ifchange target` instead.

The reasons I like this arrangement come down to semantics:

- "make target" implies that if target exists, you're done;
  conversely, "redo target" in English implies you really
  want to *redo* it, not just sit around.
  
- If this weren't the rule, `redo` and `redo-ifchange`
  would mean the same thing, which seems rather confusing.
  
- If `redo` could refuse to run a .do script, you would
  have no easy one-line way to force a particular target to
  be rebuilt.  You'd have to remove the target and *then*
  redo it, which is more typing.  On the other hand, nobody
  actually types "redo foo.o" if they honestly think foo.o
  doesn't need rebuilding.
  
- For "contentless" targets like "test" or "clean", it would
  be extremely confusing if they refused to run just
  because they ran successfully last time.
  
In make, things get complicated because it doesn't
differentiate between these two modes.  Makefile rules
with no dependencies run every time, *unless* the target
exists, in which case they run never, *unless* the target
is marked ".PHONY", in which case they run every time.  But
targets that *do* have dependencies follow totally
different rules.  And all this is needed because there's no
way to tell make, "Listen, I just really want you to run
the rules for this target *right now*."

With redo, the semantics are really simple to explain.  If
your brain has already been fried by make, you might be
surprised by it at first, but once you get used to it, it's
really much nicer this way.


# Can I write .do files in my favourite language, not sh?

Yes.  If the first line of your .do file starts with the
magic "#!/" sequence (eg. `#!/usr/bin/python`), then redo
will execute your script using that particular interpreter.

Note that this is slightly different from normal Unix
execution semantics. redo never execs your script directly;
it only looks for the "#!/" line.  The main reason for this
is so that your .do scripts don't have to be marked
executable (chmod +x).  Executable .do scripts would
suggest to users that they should run them directly, and
they shouldn't; .do scripts should always be executed
inside an instance of redo, so that dependencies can be
tracked correctly.

WARNING: If your .do script *is* written in Unix sh, we
recommend *not* including the `#!/bin/sh` line.  That's
because there are many variations of /bin/sh, and not all
of them are POSIX compliant.  redo tries pretty hard to
find a good default shell that will be "as POSIXy as
possible," and if you override it using #!/bin/sh, you lose
this benefit and you'll have to worry more about
portability.


# Can a single .do script generate multiple outputs?

FIXME: Yes, but this is a bit imperfect.

For example, compiling a .java file produces a bunch of .class
files, but exactly which files?  It depends on the content
of the .java file.  Ideally, we would like to allow our .do
file to compile the .java file, note which .class files
were generated, and tell redo about it for dependency
checking.

However, this ends up being confusing; if myprog depends
on foo.class, we know that foo.class was generated from
bar.java only *after* bar.java has been compiled.  But how
do you know, the first time someone asks to build myprog,
where foo.class is supposed to come from?

So we haven't thought about this enough yet.

Note that it's *okay* for a .do file to produce targets
other than the advertised one; you just have to be careful. 
You could have a default.javac.do that runs 'javac
$2.java', and then have your program depend on a bunch of .javac
files.  Just be careful not to depend on the .class files
themselves, since redo won't know how to regenerate them.

This feature would also be useful, again, with ./configure:
typically running the configure script produces several
output files, and it would be nice to declare dependencies
on all of them.


# Should I use environment variables to affect my build?

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
	echo "gcc -c -o \$3 \$2.c $CFLAGS" >$3
	chmod a+x $3

Then, your `default.o.do` can simply look like this:

	redo-ifchange compile $2.c
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
expansions every time it compiles a file.  Because of the
way make does expansions as macros instead of as normal
variables, this can be slow.


# Example default.o.do for both C and C++ source?

We can upgrade the compile.do from the previous answer to
look something like this:

        redo-ifchange config.sh
        . ./config.sh
        cat <<-EOF
                [ -e "\$2.cc" ] && EXT=.cc || EXT=.c
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
before it actually builds your program.  Is there a %.s?  A
%.cpp?  A %.pas?  It needs to look for *all* of them, and
it gets slow.  The more implicit rules you have, the slower
make gets.

In redo, it's not implicit at all; you're specifying exactly how to
decide whether it's a C program or a C++ program, and what to do in each
case.  Plus you can share the two gcc command lines between the two rules,
which is hard in make.  (In GNU make you can use macro functions, but the
syntax for those is ugly.)


# Can I just rebuild just part of a project?

Absolutely!  Although `redo` runs "top down" in the sense of one .do file
calling into all its dependencies, you can start at any point in the
dependency tree that you want.

Unlike recursive make, no matter which subdir of your project you're in when
you start, `redo` will be able to build all the dependencies in the right
order.

Unlike non-recursive make, you don't have to jump through any strange hoops
(like adding, in each directory, a fake Makefile that does `make -C ${TOPDIR}`
back up to the main non-recursive Makefile).  redo just uses `filename.do`
to build `filename`, or uses `default*.do` if the specific `filename.do`
doesn't exist.

When running any .do file, `redo` makes sure its current directory is set to
the directory where the .do file is located.  That means you can do this:

	redo ../utils/foo.o
	
And it will work exactly like this:

	cd ../utils
	redo foo.o
	
In make, if you run

	make ../utils/foo.o
	
it means to look in ./Makefile for a rule called
../utils/foo.o... and it probably doesn't have such a
rule.  On the other hand, if you run

	cd ../utils
	make foo.o
	
it means to look in ../utils/Makefile and look for a rule
called foo.o.  And that might do something totally
different!  redo combines these two forms and does
the right thing in both cases.

Note: redo will always change to the directory containing
the .do file before trying to build it.  So if you do

	redo ../utils/foo.o

the ../utils/default.o.do file will be run with its current directory set to
../utils.  Thus, the .do file's runtime environment is
always reliable.

On the other hand, if you had a file called ../default.o.do,
but there was no ../utils/default.o.do, redo would select
../default.o.do as the best matching .do file.  It would
then run with its current directory set to .., and tell
default.o.do to create an output file called "utils/foo.o"
(that is, foo.o, with a relative path explaining how to
find foo.o when you're starting from the directory
containing the .do file).

That sounds a lot more complicated than it is.  The results
are actually very simple: if you have a toplevel
default.o.do, then all your .o files will be compiled with
$PWD set to the top level, and all the .o filenames passed
as relative paths from $PWD.  That way, if you use relative
paths in -I and -L gcc options (for example), they will
always be correct no matter where in the hierarchy your
source files are.


# Can I put my .o files in a different directory from my .c files?

Yes.  There's nothing in redo that assumes anything about
the location of your source files.  You can do all sorts of
interesting tricks, limited only by your imagination.  For
example, imagine that you have a toplevel default.o.do that looks
like this:

	ARCH=${1#out/}
	ARCH=${ARCH%%/*}
	SRC=${1#out/$ARCH/}
	redo-ifchange $SRC.c
	$ARCH-gcc -o $3 -c $SRC.c

If you run `redo out/i586-mingw32msvc/path/to/foo.o`, then
the above script would end up running

	i586-mingw32msvc-gcc -o $3 -c path/to/foo.c

You could also choose to read the compiler name or options from
out/$ARCH/config.sh, or config.$ARCH.sh, or use any other
arrangement you want.

You could use the same technique to have separate build
directories for out/debug, out/optimized, out/profiled, and so on.


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
created by running ./configure.  The second part is easy; just write a
config.h.do that depends on the existence of configure (which is created by
configure.do, which probably runs autoconf).

The first part, however, is not so easy.  Normally, the headers that a C
file depends on are detected as part of the compilation process.  That works
fine if the headers, themselves, don't need to be generated first.  But if
you do

	redo foo.o
	
There's no way for redo to *automatically* know that compiling foo.c
into foo.o depends on first generating config.h.

Since most .h files are *not* auto-generated, the easiest
thing to do is probably to just add a line like this to
your default.o.do:

	redo-ifchange config.h
	
Sometimes a specific solution is much easier than a general
one.

If you really want to solve the general case,
[djb has a solution for his own
projects](http://cr.yp.to/redo/honest-nonfile.html), which is a simple
script that looks through C files to pull out #include lines.  He assumes
that `#include <file.h>` is a system header (thus not subject to being
built) and `#include "file.h"` is in the current directory (thus easy to
find).  Unfortunately this isn't really a complete
solution, but at least it would be able to redo-ifchange a
required header before compiling a program that requires
that header.
