# Parallelism if more than one target depends on the same subdir

Recursive make is especially painful when it comes to
parallelism.  Take a look at this Makefile fragment:

	all: fred bob
	subproj:
		touch $@.new
		sleep 1
		mv $@.new $@
	fred:
		$(MAKE) subproj
		touch $@
	bob:
		$(MAKE) subproj
		touch $@

If we run it serially, it all looks good:

	$ rm -f subproj fred bob; make --no-print-directory
	make subproj
	touch subproj.new
	sleep 1
	mv subproj.new subproj
	touch fred
	make subproj
	make[1]: 'subproj' is up to date.
	touch bob
	
But if we run it in parallel, life sucks:

	$ rm -f subproj fred bob; make -j2 --no-print-directory
	make subproj
	make subproj
	touch subproj.new
	touch subproj.new
	sleep 1
	sleep 1
	mv subproj.new subproj
	mv subproj.new subproj
	mv: cannot stat 'ubproj.new': No such file or directory
	touch fred
	make[1]: *** [subproj] Error 1
	make: *** [bob] Error 2
	
What happened?  The sub-make that runs `subproj` ended up
getting twice at once, because both fred and bob need to
build it.

If fred and bob had put in a *dependency* on subproj, then
GNU make would be smart enough to only build one of them at
a time; it can do ordering inside a single make process. 
So this example is a bit contrived.  But imagine that fred
and bob are two separate applications being built from the
same toplevel Makefile, and they both depend on the library
in subproj.  You'd run into this problem if you use
recursive make.

Of course, you might try to solve this by using
*nonrecursive* make, but that's really hard.  What if
subproj is a library from some other vendor?  Will you
modify all their makefiles to fit into your nonrecursive
makefile scheme?  Probably not.

Another common workaround is to have the toplevel Makefile
build subproj, then fred and bob.  This works, but if you
don't run the toplevel Makefile and want to go straight
to work in the fred project, building fred won't actually
build subproj first, and you'll get errors.

redo solves all these problems.  It maintains global locks
across all its instances, so you're guaranteed that no two
instances will try to build subproj at the same time.  And
this works even if subproj is a make-based project; you
just need a simple subproj.do that runs `make subproj`.


# Dependency problems that only show up during parallel builds

One annoying thing about parallel builds is... they do more
things in parallel.  A very common problem in make is to
have a Makefile rule that looks like this:

	all: a b c
	
When you `make all`, it first builds a, then b, then c. 
What if c depends on b?  Well, it doesn't matter when
you're building in serial.  But with -j3, you end up
building a, b, and c at the same time, and the build for c
crashes.  You *should* have said:

	all: a b c
	c: b
	b: a
	
and that would have fixed it.  But you forgot, and you
don't find out until you build with exactly the wrong -j
option.

This mistake is easy to make in redo too.  But it does have
a tool that helps you debug it: the --shuffle option. 
--shuffle takes the dependencies of each target, and builds
them in a random order.  So you can get parallel-like
results without actually building in parallel.


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

The problem:

This idea won't work as easily with redo as it did with
make.  With make, a separate copy of $SHELL is launched for
each step of the build (and gets migrated to the remote
machine), but make runs only on your local machine, so it
can control parallelism and avoid building the same target
from multiple machines, and so on.  The key to the above
distribution mechanism is it can send files to the remote
machine at the beginning of the $SHELL, and send them back
when the $SHELL exits, and know that nobody cares about
them in the meantime.  With redo, since the entire script
runs inside a shell (and the shell might not exit until the
very end of the build), we'd have to do the parallelism
some other way.

I'm sure it's doable, however.  One nice thing about redo
is that the source code is so small compared to make: you
can just rewrite it.


# Can I convince a sub-redo or sub-make to *not* use parallel builds?

Yes.  Put this in your .do script:

	unset MAKEFLAGS
	
The child makes will then not have access to the jobserver,
so will build serially instead.
