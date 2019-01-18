# Is redo compatible with autoconf?

Yes.  You don't have to do anything special, other than the above note about
declaring dependencies on config.h, which is no worse than what you would
have to do with make.


# Is redo compatible with automake?

Hells no.  You can thank me later.  But see next question.


# Is redo compatible with make?

Yes.  If you have an existing Makefile (for example, in one of your
subprojects), you can just call make from a .do script to build that
subproject.

In a file called myproject.stamp.do:

	redo-ifchange $(find myproject -name '*.[ch]')
	make -C myproject all

So, to amend our answer to the previous question, you *can* use
automake-generated Makefiles as part of your redo-based project.


# Is redo -j compatible with make -j?

Yes!  redo implements the same jobserver protocol as GNU make, which means
that redo running under make -j, or make running under redo -j, will do the
right thing.  Thus, it's safe to mix-and-match redo and make in a recursive
build system.

Just make sure you declare your dependencies correctly;
redo won't know all the specific dependencies included in
your Makefile, and make won't know your redo dependencies,
of course.

One way of cheating is to just have your make.do script
depend on *all* the source files of a subproject, like
this:

	make -C subproject all
	find subproject -name '*.[ch]' | xargs redo-ifchange

Now if any of the .c or .h files in subproject are changed,
your make.do will run, which calls into the subproject to
rebuild anything that might be needed.  Worst case, if the
dependencies are too generous, we end up calling 'make all'
more often than necessary.  But 'make all' probably runs
pretty fast when there's nothing to do, so that's not so
bad.
