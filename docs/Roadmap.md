We believe that, unlike most programs, it's actually possible to "finish"
redo, in the sense of eventually not needing to extend its semantics or add
new features.  That's because redo is a pretty low-level system that just
provides some specific features (dependency checking, parallelism, log
linearization, inter-process locking).  It's the job of your build scripts
to tie those features together in the way you want.

`make` has its own imperative syntax, which creates a temptation to add
new built-in functions and syntax extensions.  In more
"declarative" build systems, there's a constant need to write new extension
modules or features in order to create functionality that wasn't available
declaratively.  redo avoids that by using a turing-complete language
to run your builds.  You should be able to build anything at all with redo,
just by writing your .do scripts the way you want.

Thus, the only things that need to be added to redo (other than portability
and bug fixes, which will likely be needed forever) are to fix gaps in
redo's model that prevent you from getting your work done.  This document
describes the gaps we're currently aware of.

Note that all of the items in this document are still unimplemented.  In
most cases, that's because we haven't yet settled on a final design, and
it's still open to discussion.  The place to discuss design issues is the
[mailing list](../Contributing/#mailing-list).


### default.do search path, and separated build directories

One of the most controversial topics in redo development, and for developers
trying to use redo, is: where do you put all those .do scripts?

redo searches hierarchically up the directory tree from a target's filename,
hoping to find a `default*.do` file that will match, and then uses the first
one it finds.  This method is rather elegant when it works.  But many
developers would like to put their output files into a separate directory
from their source files, and that output directory might not be a
subdirectory of the main project (for example, if the main project is on a
read-only filesystem).

There are already a few ways to make this work, such as placing a single
`default.do` "proxy" or "delegation" script at the root of the output
directory, which will bounce requests to .do files it finds elsewhere.  One
nice thing about this feature is it doesn't require any changes to redo
itself; redo already knows how to call your toplevel default.do script.
However, some people find the delegation script to be inelegant and
complicated.

Other options include searching inside a known subdirectory name (eg.
`do/`), which could be a symlink; or adding a `.dopath` file which tells
redo to search elsewhere.

So far, we haven't settled on the best design, and discussion is welcome.
In the meantime, you can write a delegation script (TODO: link to example)
for your project.  Because this requires no special redo features, it's
unlikely to break in some later version of redo, even if we add a new
method.


### .do files that produce directories

Sometimes you want a .do file to produce multiple output files in a single
step.  One example is an autoconf `./configure` script, which might produce
multiple files.  Or, for example, look at the [LaTeX typesetting
example](../cookbook/latex/) in the redo cookbook.

In the purest case, generating multiple outputs from a single .do file
execution violates the redo semantics.  The design of redo calls for
generating *one* output file from *zero or more* input files.  And most of
the time, that works fine. But sometimes it's not enough.

Currently (like in the LaTeX example linked above) we need to resolve this
problem by taking advantage of "side effects" in redo: creating a set of
files that are unknown to redo, but sit alongside the "known" files in the
filesystem.  But this has the annoying limitation that you cannot
redo-ifchange directly on the file you want, if it was generated this way.
For example, if `runconfig.do` generates `Makefile` and `config.h`, you
must not `redo-ifchange config.h` directly; there is no .do file for
`config.h`.  You must `redo-ifchange runconfig` and then *use*
`config.h`.

(There are workarounds for that workaround: for example, `runconfig.do`
could put all its output files in a `config/` directory, and then you could
have a `config.h.do` that does `redo-ifchange runconfig` and `cp
config/config.h $3`.  Then other scripts can `redo-ifchange config.h`
without knowing any more about it.  But this method gets tedious.)

One suggestion for improving the situation would be to teach redo about
"directory" targets.  For example, maybe we have a `config.dir.do` that
runs `./configure` and produces files in a directory named `config`.  The
`.dir.do` magic suffix tells redo that if someone asks for
`config/config.h`, it must first try to instantiate the directory named
`config` (using `config.dir.do`), and only then try to depend on the file
inside that directory.

There are a number of holes in this design, however.  Notably, it's not
obvious how redo should detect when to activate the magic directory feature.
It's easy when there is a file named `config.dir.do`, but much less obvious
for a file like `default.dir.do` that can construct certain directory types,
but it's not advertised which ones.

This particular cure may turn out to be worse than the disease.


### Per-target-directory .redo database

An unexpectedly very useful feature of redo is the ability to "redo from
anywhere" and get the same results:
```shell
	$ cd /a/b/c
	$ redo /x/y/z/all
```
should have the same results as
```shell
	$ cd /x/y/z
	$ redo all
```

Inside a single project, this already works.  But as redo gets used more
widely, and in particular when you have multiple redo-using projects that
want to refer to other redo-using projects, redo can get confused about
where to put its `.redo` state database.  Normally, it goes into a directory
called `$REDO_BASE`, the root directory of your project.  But if a .do
script refers to a directory outside or beside the root, this method doesn't
work, and redo gets the wrong file state information.

Further complications arise in the case of symlinks.  For example, if you
ask redo to build `x/y/z/file` but `y` is a symlink to `q`, then redo will
effectively end up replacing `x/q/z/file` when it replces `x/y/z/file`,
since they're the same.  If someone then does `redo-ifchange x/q/z/file`,
redo may become confused about why that file has "unexpectedly" changed.

The fix for both problems is simple: put one `.redo` database in every
directory that contains target files.  The `.redo` in each directory
contains information only about the targets in that directory.  As a result,
`x/y/z/file` and `x/q/z/file` will share the same state database,
`x/q/z/.redo`, and building either target will update the state database's
understanding of the file called `file` in the same directory, and there
will be no confusion.

Similarly, one redo-using project can refer to targets in another redo-using
project with no problem, because redo will no longer have the concept of a
`$REDO_BASE`, so there is no way to talk about targets "outside" the
`$REDO_BASE`.

Note that there is no reason to maintain a `.redo` state database in
*source* directories (which might be read-only), only target directories.
This is because we store `stat(2)` information for each dependency anyway, so
it's harmless if multiple source filenames are aliases for the same
underlying content.


### redo-{sources,targets,ood} should take a list of targets

With the above change to a per-target-directory `.redo` database, the
original concept of the `redo-sources`, `redo-targets`, and `redo-ood`
commands needs to change.  Currently they're defined to list "all" the
sources, targets, and out-of-date targets, respectively.  But when there is
no single database reflecting the entire filesystem, the concept of "all"
becomes fuzzy.

We'll have to change these programs to refer to "all (recursive)
dependencies of targets in the current directory" by default, or of all
targets listed on the command line otherwise.  This is probably more useful
than the current behaviour anyway, since in a large project, one rarely
wants to see a complete list of all sources and targets.


### Deprecating "stdout capture" behaviour

The [original design for redo](http://cr.yp.to/redo.html) specified that a
.do script could produce its output either by writing to stdout, or by
writing to the file named by the `$3` variable.

Experience has shown that most developers find this very confusing.  In
particular, results are undefined if you write to *both* stdout and `$3`.
Also, many programs (including `make`!) write their log messages to stdout
when they should write to stderr, so many .do scripts need to start with
`exec >&2` to avoid confusion.

In retrospect, automatically capturing stdout was probably a bad idea.  .do
scripts should intentionally redirect to `$3`.  To enforce this, we could
have redo report an error whenever a .do script returns after writing to its
stdout.  For backward compatibility, we could provide a command-line option
to downgrade the error to a warning.


### Deprecating environment variable sharing

In redo, it's considered a poor practice to pass environment variables (and
other process attributes, like namespaces) from one .do script to another.
This is because running `redo-ifchange /path/to/file` should always run
`file`'s .do script with exactly the same settings, whether you do it from
the toplevel from from deep inside a tree of dependencies.  If an
environment variable set in one .do script can change what's seen by an
inner .do script, this breaks the dependency mechanism and makes builds less
repeatable.

To make it harder to do this by accident, redo could intentionally wipe all
but a short whitelist of allowed environment variables before running any
.do script.

As a bonus, by never sharing any state outside the filesystem, it becomes
much more possible to make a "distributed redo" that builds different
targets on different physical computers.


### redo-recheck command

Normally, redo only checks any given file dependency at most once per
session, in order to reduce the number of system calls executed, thus
greatly speeding up incremental builds.  As a result, `redo-ifchange` of the
same target will only execute the relevant .do script at most once per
session.

In some situations, notably integration tests, we want to force redo to
re-check more often.  Right now there's a hacky script called
`t/flush-cache` in the redo distribution which does this, but it relies on
specific knowledge of the .redo directory's database format, which means it
only works in this specific version of redo; this prevents the integration
tests from running (and thus checking compatibility with) competing redo
implementations.

If we standardized a `redo-recheck` command, which would flush the cache for
the targets given on the command line, and all of their dependencies, this
sort of integration test could work across multiple redo versions.  For redo
versions which don't bother caching, `redo-recheck` could be a null
operation.


### tty input

Right now, redo only allows a .do file to request input from the user's
terminal if using `--no-log` and *not* using the `-j` option.  Terminal
input is occasionally useful for `make config` interfaces, but parallelism
and log linearization make the console too cluttered for a UI to work.

The ninja build system has a [console
pool](https://ninja-build.org/manual.html#_the_literal_console_literal_pool)
that can contain up to one job at a time.  When a job is in the console
pool, it takes over the console entirely.

We could probably implement something similar in redo by using POSIX job
control features, which suspend subtasks whenever they try to read
from the tty.  If we caught the suspension signal and acquired a lock, we
could serialize console access.

Whether the complexity of this feature is worthwhile is unclear.  Maybe it
makes more sense just to have a './configure' script that runs outside the
redo environment, but still can call into redo-ifchange if needed.


### redo-lock command

Because it supports parallelism via recursion, redo automatically handles
inter-process locking so that only one instance of redo can try to build a
given target at a time.

This sort of locking turns out to be very useful, but there are a few
situations where requiring redo to "build a target by calling a .do file" in
order to acquire a lock becomes awkward.

For example, imagine redo is being used to call into `make` to run arbitrary
`Makefile` targets.  `default.make.do` might look like this:
```sh
make "$2"
```

redo will automatically prevent two copies of `redo all.make` from running
at once.  However, if someone runs `redo all.make myprogram.make`, then two
copies of `make` will execute at once.  This *might* be harmless, but if the
`all` target in the `Makefile` has a dependency on `myprogram`, then we will
actually end up implicitly building `myprogram` from two places at once:
from the `myprogram` part of `all.make` and from `myprogram.make`.

In hairy situations like that, it would be nice to serialize all access
inside `default.make.do`, perhaps like this:
```sh
redo-lock make.lock make "$2"
```

This would create a redo-style lock on the (virtual) file `make.lock`, but
then instead of trying to `redo make.lock`, it would run the given command,
in this case `make "$2"`.

It's unclear whether this feature is really a good idea.  There are other
(convoluted) ways to achieve the same goal.  Nevertheless, it would be easy
enough to implement.  And redo versions that don't support parallelism could
just make redo-lock a no-op, since they guarantee serialization in all cases
anyway.


### Include a (minimal) POSIX shell

A common problem when writing build scripts, both in `make` and in redo, is
gratuitous incompatibility between all the available POSIX-like unix shells.
Nowadays, most shells support [various pure POSIX sh
features](https://apenwarr.ca/log/20110228), but there are always glitches.
In some cases, POSIX doesn't define the expected behaviour for certain
situations.  In others, shells like `bash` try to "improve" things by
changing the syntax in non-POSIX ways.  Or maybe they just add new
backward-compatible features, which you then rely on accidentally because
you only tested your scripts with `bash`.

redo on Windows using something like [MSYS](http://www.mingw.org/wiki/msys)
is especially limited by the lack of (and oddity of) available unix tools.

To avoid all these portability problems for .do script maintainers, we might
consider bundling redo with a particular (optional) sh implementation, and
maybe also unix-like tools, that it will use by default.  An obvious
candidate would be busybox, which has a win32 version called
[busybox-w32](https://frippery.org/busybox/).
