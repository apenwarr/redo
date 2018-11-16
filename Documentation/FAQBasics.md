# Does redo make cross-platform builds easy?

A lot of build systems that try to replace make do it by trying to provide a
lot of predefined rules.  For example, one build system I know includes
default rules that can build C++ programs on Visual C++ or gcc,
cross-compiled or not cross-compiled, and so on.  Other build systems are
specific to ruby programs, or python programs, or Java or .Net programs.

redo isn't like those systems; it's more like make.  It doesn't know
anything about your system or the language your program is written in.

The good news is: redo will work with *any* programming language with about
equal difficulty.  The bad news is: you might have to fill in more details
than you would if you just use ANT to compile a Java program.

So the short version is: cross-platform builds are about equally easy in
make and redo.  It's not any easier, but it's not any harder.

It would be possible to make an automake-like or cmake-like tool that
generates .do files for your project, just like automake generates
Makefiles.  But that's beyond the scope of redo itself.


# Can I set my dircolors to highlight .do files in ls output?

Yes!  At first, having a bunch of .do files in each
directory feels like a bit of a nuisance, but once you get
used to it, it's actually pretty convenient; a simple 'ls'
will show you which things you might want to redo in any
given directory.

Here's a chunk of my .dircolors.conf:

	.do 00;35
	*Makefile 00;35
	.o 00;30;1
	.pyc 00;30;1
	*~ 00;30;1
	.tmp 00;30;1

To activate it, you can add a line like this to your .bashrc:

	eval `dircolors $HOME/.dircolors.conf`


# Do end users have to have redo installed in order to build my project?

No.  We include a very short and simple shell script
called `do` in the `minimal/` subdirectory of the redo project.  `do` is like
`redo` (and it works with the same `*.do` scripts), except it doesn't
understand dependencies; it just always rebuilds everything from the top.

You can include `do` with your program to make it so non-users of redo can
still build your program.  Someone who wants to hack on your program will
probably go crazy unless they have a copy of `redo` though.

Actually, `redo` itself isn't so big, so for large projects where it
matters, you could just include it with your project.


# Recursive make is considered harmful.  Isn't redo even *more* recursive?

You probably mean [this 1997 paper](http://miller.emu.id.au/pmiller/books/rmch/)
by Peter Miller.

Yes, redo is recursive, in the sense that every target is built by its own
`.do` file, and every `.do` file is a shell script being run recursively
from other shell scripts, which might call back into `redo`.  In fact, it's
even more recursive than recursive make.  There is no
non-recursive way to use redo.

However, the reason recursive make is considered harmful is that each
instance of make has no access to the dependency information seen by the
other instances.  Each one starts from its own Makefile, which only has a
partial picture of what's going on; moreover, each one has to
stat() a lot of the same files over again, leading to slowness.  That's
the thesis of the "considered harmful" paper.

It turns out that [non-recursive make should also be considered harmful](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/03/hadrian.pdf).
The problem is Makefiles aren't
very "hygienic" or "modular"; if you're not running make recursively, then
your one copy of make has to know *everything* about *everything* in your
entire project.  Every variable in make is global, so every variable defined
in *any* of your Makefiles is visible in *all* of your Makefiles.  Every
little private function or macro is visible everywhere.  In a huge project
made up of multiple projects from multiple vendors, that's just not okay.
Plus, if all your Makefiles are tangled together, make has
to read and parse the entire mess even to build the
smallest, simplest target file, making it slow.

`redo` deftly dodges both the problems of recursive make
and the problems of non-recursive make.  First of all,
dependency information is shared through a global persistent `.redo`
database, which is accessed by all your `redo` instances at once. 
Dependencies created or checked by one instance can be immediately used by
another instance.  And there's locking to prevent two instances from
building the same target at the same time.  So you get all the "global
dependency" knowledge of non-recursive make.  And it's a
binary file, so you can just grab the dependency
information you need right now, rather than going through
everything linearly.

Also, every `.do` script is entirely hygienic and traceable; `redo`
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
paper's complaints.  `redo` runs your scripts from top to bottom in a
nice tree, so it's traceable no matter how many layers you have.
