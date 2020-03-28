### redoconf: Platform detection and C/C++ programs

In the redo source tree you can now find a companion toolkit, redoconf,
which provides a handy way to build C and C++ programs that work on
different Unix variants and Windows 10's WSL (Windows Subsystem for Linux),
including the ability to use cross compilers and to compile the same source
tree for multiple platforms in different output directories.

(redo and redoconf probably also work on Cygwin or MSYS on Windows, but
these are less well tested.)

In this tutorial, we'll construct a new cross-platform-capable C++ project
from scratch, step by step, using redo and redoconf.

### Intended for copy-and-paste

redoconf is intended to be used by copying it directly into your source
repository, not by adding it as an external dependency. Otherwise you have a
chicken-and-egg problem: redoconf is the dependency checking and platform
independence tool, so how will you check for redoconf on your user's
platform?

redoconf also does not make backward-compatibility guarantees in the same
way that redo does.  With redo, we try very hard to ensure that when a new
version comes out, all programs that used to build with redo will continue
to build just fine; all new features must not interfere with old behaviour.
With redoconf, we don't make this promise.  Upgrading redoconf might break
your project in small ways, so you have to change a few things (hopefully
for the better).  We still try not to break things, but it's not a promise
like it is with redo.

In these ways (copy-and-paste design; no compatibility guarantees), redoconf
is very much like autoconf and automake, and that's on purpose. Those very
intentional design decisions have made those programs successful for decades.

That said, we do depart slightly from how autoconf and automake work. Those
packages provide command-line tools which *generate* customized files into
your source tree.  This was important because they depend on the M4 macro
processor, which not everyone has available, and moreover, they wanted to
use autoconf to configure the source code for GNU M4, so they had an even
deeper chicken-and-egg problem.

But they didn't have redo. Because redo's interface is so simple -
implemented in
[minimal/do](/FAQBasics/#do-end-users-have-to-have-redo-installed-in-order-to-build-my-project)
in a few hundred lines of shell script - and redo is powerful enough to run
the entire build system, we can use redo instead of M4 macros. And we can
use minimal/do when building redo, which means we can use redoconf to build
redo, and there are no circular dependencies.

Anyway, the net result is that instead of *generating* customized files into
your source project like autoconf does, you can just *copy* the redoconf
files verbatim into a redoconf subdirectory of your project, and later
update them to a new version later in the same way.

Let's do that as the first step to building our C++ test project.  If you
want to play with the completed results, get the [redo
source code](https://github.com/apenwarr/redo) and look in the
`docs/cookbook/redoconf-simple/` directory.  (Note: in that directory,
redoconf is a symlink rather than a copy, because the redo source repo
already contains a copy of redoconf.)


### Paste redoconf into your project

Let's get started!  (Replace `/path/to/redo` in this example with the path
to your copy of the redo source code, or the directory containing the
redoconf you want to copy.)
```shell
$ mkdir redoconf-simple
$ cd redoconf-simple
$ cp -a /path/to/redo/redoconf redoconf
```

Now we have to provide a `configure` script.  It doesn't do much other than
call into `configure.sh` inside the redoconf directory.
<pre><code lang='sh' src='configure'></code></pre>

(One important job the configure script does is to provide a value for `$S`,
the path to the top of the source tree, relative to the output directory.
The convention with autoconf, which we copy here, is to always *run*
configure from the directory where you want to produce the output.  Then the
path to the configure program - which is in `$0` - will also be the path to
the source directory.  To make this work, you need a configure script to be
in the top level of your source directory.)

As you can see, unlike autoconf, which generates a new configure script for
your specific project, our configure script is just a few lines of
boilerplate.


### Run ./configure

redoconf is ready to go!  Let's configure it and see what it can detect.
```shell
$ ./configure
./configure: run this script from an empty output directory.
  For example:
    (mkdir out && cd out && ../configure && redo -j10)
```

Oops.  Unlike autoconf, redoconf strongly encourages you to create a
*separate* output directory from the rest of your source code.  Autoconf
lets you get away with building your source and output in the same place.
As a result, users often don't even know it supports separate source and
output directories.  But even worse, developers often don't *test* its
behaviour with separate source and output directories, which sometimes
causes them to break the feature by accident.  To cut down on variation,
redoconf just always pushes you to use a separate output directory, and
gives you a hint for how to use it.  Let's run the command it suggested,
except we'll skip the `redo` part since there is nothing to redo yet.
```shell
$ (mkdir out && cd out && ../configure)
```

No output.  In the unix tradition, that means it worked.

We've departed again from autoconf here.  When you run an autoconf
configure script, it immediately tries to detect everything it needs.  This
is necessary because autoconf is independent of make; it wants to detect
things *before* you run make, and is usually responsible for generating your
Makefile.

On the other hand, redoconf fundamentally depends on redo - or at least
[minimal/do](/FAQBasics/#do-end-users-have-to-have-redo-installed-in-order-to-build-my-project).
That's mostly good news because, for example, it can run its detection
scripts in parallel using redo's parallelism features, thus making it much
faster than autoconf on modern machines. But on the other hand, it doesn't
want to force you to use any particular version of redo. You might use
minimal/do, or the "official" redo whose documentation you are reading
(sometimes known as apenwarr/redo), or some other compatible version. In
order to avoid that choice, the redoconf configure script just sets up the
output directory and then quits.

So okay, if the detection is going to be done by redo anyway, why do we even
need a configure script?

Good question! The reason is that redo scripts (.do files) don't take
command-line parameters. Redo tries very hard to make the build process for
each target completely repeatable, so that you can `redo path/to/whatever`
and have it build the `whatever` output file in exactly the same way as if
you did `cd path/to && redo whatever` or if `redo all` calls
`path/to/whatever` as one of its dependencies.

When you're starting to build a project, though, sometimes you need to
provide command line options.  One of them is the implicit one we mentioned
above: the current directory, at the time you run the configure script, is
recorded to be the output directory.  And from there, we remember `$S`,
which is the relative path to the source tree.  But there are other options,
too:
```shell
$ (cd out && ../configure --help)
Usage: ../configure [options...] [KEY=value] [--with-key=value]

    --prefix=       Change installation prefix (usually /usr/local)
    --host=         Architecture prefix for output (eg. i686-w64-mingw32-)
    --enable-static               Link binaries statically
    --disable-shared              Do not build shared libraries
    --{dis,en}able-optimization   Disable/enable optimization for C/C++
    --{dis,en}able-debug          Disable/enable debugging flags for C/C++
    -h, --help      This help message

No extra help yet: configure.help is missing.
```

This project doesn't have any files yet, so the option list is pretty short.
But a very important one is `--host`, which lets you specify which
cross-compiler to use.  (The name `--host` is also copied from autoconf, and
has a very confusing history that dates back to the early gcc project.  It
means the "host architecture" of the programs that we will produce.  Despite
the confusion, we decided to stick with the autoconf naming convention here.
A name like `--target` might be more obvious, but in autoconf that means
something else entirely.)

Anyway, to get started, we didn't provide any options, so we'll get the
defaults.  The configure script then configured our output directory for us
by creating a few files:
```shell
$ ls out
Makefile  _flags  default.do@  redoconf.rc  src

$ cat out/_flags
# Auto-generated by ../configure

$ cat out/src
..

$ cat out/redoconf.rc
# Automatically generated by ../configure
read -r S <src
. "$S/redoconf/rc.sh"
```

The `_flags` file is empty, because we didn't give the configure script any
flags. The `src` file contains just one line, the relative path to the
source dir from the output dir, saved from `$S` in the configure script,
which is just `..` in this case. And `redoconf.rc` is a simple shell script
that you can use in a .do or .od file, or a shell script, to load the
redoconf helper functions.

We also generate a miniature makefile, which looks like this:

```shell
$ cat out/Makefile
# A wrapper for people who like to type 'make' instead of 'redo'
all $(filter-out all,$(MAKECMDGOALS)):
	+redo "$@"
.PHONY: $(MAKECMDGOALS) all
```

This makes it easier for end users, who are trying to compile your program
but don't know the difference between make and redo.  It just takes all
calls to `make anything` in the `out/` directory and passes them along to
`redo anything`.

Finally, there is a `default.do` symlink into the redoconf directory.  This
tells redo that to produce any target under `out/`, it should run
`default.do`, which lets redoconf decide how to produce the output.

### Source targets and output targets

One of the nice things about redoconf (and also autoconf) is that you can
have multiple output directories sharing a single source directory.  So when
you modify one source file, you can incrementally recompile the output for
all the platforms you're interested in.

However, the most obvious way to use redo doesn't work like that.  Usually,
you put the .do file for a target alongside the source files, all in one
directory.  When you say `redo target`, redo looks for `target.do` and runs
that.

So, we could start by having `out/default.do` just forward requests to .do
files in the source directory.  But that's not quite right either.  What
does it mean, if I have a `hello.cc` source file, and I type `redo hello.o`
in the source directory?  Nothing good.  The source directory isn't where
`hello.o` is supposed to end up.  So we want to prevent that from even
trying to work.

Conversely, some targets do *not* depend on the particular output platform.
For example, if you want to generate a list of all source files in the
project (which is frequently useful, for example if you want to
automatically compile and link all source files matching a pattern into a
single output binary), that list will not depend on the output platform, so
it would be nice to generate it just once.  In that case, it *is* meaningful
to generate it directly in the source tree.

Phew!

Luckily, making it work is not as complicated as explaining it. What we do
is write the .do files for "source targets" in the usual way: as .do files
in the source tree, next to where the target will be produced. And we write
the code for "output targets" - scripts for producing platform-specific
output files based on the source code - as .od files (.do spelled
backwards). We can't put them in the output directory, because that
directory isn't included when you distribute the source code.  So we put the
.od files in the source tree, alongside the source files and .do files.

To give some specific examples:

- To generate `a/b/c/sources.all`, we use a script called
  `a/b/c/sources.all.do`

- To generate `out/a/b/c/foo.o`, we use a script called `a/b/c/foo.o.od` (or
  more likely, `a/b/c/default.o.od` or even just `default.o.od` in the top
  level source directory).

The job of redoconf's auto-generated `default.do` is to pick the right
.do or .od file and make sure it does the right thing.


### Feature detectors

Okay, that's a lot of explanation, considering we have only done three
things:

- made a copy of redoconf in our project
- created an output directory
- run `../configure` from the output directory.

What can we do with that?

Quite a lot, in fact.

Redoconf is based around the concept of "detector modules," which is a fancy
name for a set of shell scripts that each can detect a compiler, a platform
feature, or an available library or header files.

Autoconf has a very similar concept, but detector modules are written in the
arcane M4 macro language, which expands out into an auto-generated configure
script, which then runs the necessary detectors sequentially.  Redoconf, in
the redo tradition, runs each detector as a separate redo target which
produces its detection results into a small file.  And they can be run in
parallel, and can have dependencies on other targets or any other source or
target files in the project.

Let's try one of the built-in detectors:
```shell
$ cd out

$ redo rc/CC.rc
redo  rc/CC.rc
redo    rc/_init.rc
Trying C compiler: 'cc'
  CPPFLAGS += '-I.'
  CC = 'cc'
  LINK = 'cc'
  ARCH = ''
  HAVE_CC = '1'
```

The output of a redoconf detector is an "rc" file, based on a very, very
long unix tradition (including /etc/rc, /etc/rc3.d, the plan9 rc shell, and
others). Nobody is quite sure what "rc" stands for, but some people suggest
it might be "Run Commands" or "ResourCe" or, in this case, RedoConf. What
people do agree about is that "rc" files are supposed to be configuration
information in a format that can be read by the shell.

Let's look at what got produced in this case:
```shell
$ cat rc/CC.rc
rc_include rc/_init.rc
helpmsg ARCH 'Architecture prefix for output (eg. i686-w64-mingw32-)'
helpmsg CC 'C compiler name (cc)'
helpmsg CPPFLAGS 'Extra C preprocessor flags (eg. -I... -D...)'
helpmsg CFLAGS 'Extra C compiler flags (eg. -O2 -g)'
helpmsg OPTFLAGS 'C/C++ compiler flag overrides (eg. -g0)'
helpmsg LINK 'Linker name (cc)'
helpmsg LDFLAGS 'Extra linker options (eg. -s -static)'
helpmsg LIBS 'Extra libraries to always link against (eg. -lsocket)'
helpmsg STATIC 'Link libraries and binaries statically'
appendln CPPFLAGS '-I.'
replaceln CC 'cc'
replaceln LINK 'cc'
replaceln ARCH ''
replaceln HAVE_CC '1'
```

Without going into detail about the syntax, what this means is that `CC.rc`
- the C compiler detector - depends on rc/_init.rc (the flags provided to
`configure`).  It then declares a bunch of options that you can pass to
configure; these will extend the output of `configure --help` that we saw
above, but let's get to that later.  Finally, it fills in some values
related to how to compile and link C programs on this platform.

In redoconf, all shell variables use only newlines as word separators, not
spaces or tabs. That way, we can cleanly handle file and directory names
containing spaces, all the way through the system.  (Filenames containing
newline characters are technically allowed by POSIX, but are a terrible
idea.  Just don't do that.  Redo explicitly rejects them because they're too
hard to deal with in shell scripts or .do files.)  Anyway, because of this,
redoconf provides a function for appending to a newline-separated string
(appendln) or replacing a newline-separated string (replaceln).  We use
these instead of directly reassigning the shell variables.

The idea of an rc file is that we can use it to load variables into a shell
script:
```shell
$ (. ./redoconf.rc && . rc/CC.rc && echo $CPPFLAGS)
-I.
```

It works!  And we didn't even have to create any source files first.

redoconf also provides default scripts for compiling C and C++ programs,
which we can call from `.od` files, either explicitly or automatically.
Let's ask for a compiler script:
```shell
$ redo compile
redo  compile
redo    _all.rc
redo      rc/zdefs.rc
  LDFLAGS += '-Wl,-z,defs'
redo    _compile

$ cat compile
#!/bin/sh -e
# Run the C/++ compiler.
t="$1" d="$2" i="$3"
CPPFLAGS='-I.'
OPTFLAGS=''
case $i in
  *.c|*.h)
    CC='cc'
    CFLAGS=''
    CXXFLAGS=
    PCH1=''
    PCH2=''
    PCH3=''
    ;;
  *)
    CC=''
    [ -n "$CC" ] || (echo "No C++ compiler available." >&2; exit 1)
    CFLAGS=
    CXXFLAGS=''
    PCH1=''
    PCH2=''
    PCH3=''
    ;;
esac
case $PCH in
  1) FLAGS_PCH=$PCH1 ;;
  2) FLAGS_PCH=$PCH2 ;;
  3) FLAGS_PCH=$PCH3 ;;
esac
. ./_compile

$ cat _compile
#!/bin/sh -e
# Run the C/C++ compiler.
# Assumes config variables (CFLAGS, etc) are already set.
t="$1" d="$2" i="$3"
IFS="
"
set -f
$CC -o "$t" \
  -MMD -MF "$d" \
  $CPPFLAGS $CFLAGS $CXXFLAGS $FLAGS_PCH $xCFLAGS $OPTFLAGS \
  -c "$i"
```

Let's not worry too much about these files - which are auto-generated anyway
- other than to note that they embed the actual values of things like `CC`
and `CPPFLAGS` that were detected in `rc/CC.rc`. The reason we do that is
because having the shell load our .rc files (sometimes recursively) can be a
little slow, and in a large project, we might end up doing it hundreds or
thousands of times.  It's better to do the substitution once, and produce a
`./compile` script, than to repeat the substitutions over and over.  It's
also convenient to know you can just run
`./compile hello.o.tmp hello.deps hello.cc` at any time and be
sure that it is always compiled the same way, with no impact from
environment variable settings.

### Choosing the feature detectors for our project

We cheated and skipped a step above. We can build .rc files individually,
but that doesn't automatically feed them into the `./compile` script, which
happens to only include `rc/CC.rc` by default (since it's absolutely
essential for compiling C programs).  If we want to include other compiler
options, header files, and libraries, we'll need to tell redoconf the
complete set of detectors that are relevant to our project.  We do that with
the special file `all.rc`, which is generated from `all.rc.od`.  Let's
assemble one for our example project:
<pre><code lang='sh' src='all.rc.od'></code></pre>

And here's the result:
```shell
$ redo all.rc
redo  all.rc
redo    rc/CXX.required.rc
redo      rc/CXX.rc
Trying C++ compiler: 'c++'
  CXX = 'c++'
  LINK = 'c++'
  HAVE_CXX = '1'
redo    rc/Wextra.rc
redo      rc/Wall.rc
  CPPFLAGS += '-Wall'
redo    rc/Wextra.rc (resumed)
  CPPFLAGS += '-Wextra'
redo    rc/all.hpp.precompiled.rc
  CXXFLAGS_PCH_LANG += '-x
c++-header'
  CXXFLAGS += '-Winvalid-pch'
  CXXFLAGS_PCH += '-include
all.hpp'
  CXXFLAGS_PCH_FPIC += '-include
all.hpp.fpic'
  PRE_CXX_TARGETS += 'all.hpp.gch'
  PRE_CXX_TARGETS_FPIC += 'all.hpp.fpic.gch'
redo    rc/openssl__ssl.h.rc
  HAVE_OPENSSL__SSL_H = '1'
redo    rc/openssl__opensslv.h.rc
  HAVE_OPENSSL__OPENSSLV_H = '1'
redo    rc/libssl.rc
redo      rc/pkg-config.rc
  PKG_CONFIG = 'pkg-config'
  HAVE_PKG_CONFIG = '1'
redo    rc/libssl.rc (resumed)
  CPPFLAGS += ''
  LIBSSL += '-lssl
-lcrypto'
  HAVE_LIBSSL = '1'
redo    rc/libm.rc
  HAVE_LIBM = '1'
  LIBM += '-lm'
redo  all.rc (resumed)
  LIBS += '-lssl
-lcrypto'
```

Notice the slightly odd formatting when we append multiple words to the same
variable: there is a newline separating `-lssl` and `-lcrypto`, for example.

Now that we have an `all.rc.od`, the `compile` script will have more stuff
in it.

Let's look at some examples of the built-in detector scripts we're using.
You can find them all in the `redoconf/rc/` directory.  This project won't
define any extra ones, but if you wanted to, you could put them in your own
`rc/` directory of your source tree.  If there's an overlap between your
`rc/` directory and the `redoconf/rc/` directory, yours will override the
built-in one.  So feel free to copy detectors from `redoconf/rc/` into your
own `rc/` and customize them as needed.

Here's a script that just detects whether the compiler supports gcc's
`-Wextra` (extra warnings) option.  If you use it, it also pulls in the
`-Wall` detector by default:
<pre><code lang='sh' src='redoconf/rc/Wextra.rc.od'></code></pre>

And here's the detector that checks if a given header file is available.
This is how we handle the request for `rc/openssl__ssl.h.rc` in `all.rc` for
example.  It will define `HAVE_OPENSSL__SSL_H` (the two underscores mean a
`/` character in the path) if `openssl/ssh.h` exists. <pre><code lang='sh'
src='redoconf/rc/default.h.rc.od'></code></pre>

Here's one that detects libssl (both headers, for compile time, and
libraries, for link time) using pkg-config, if available:
<pre><code lang='sh' src='redoconf/rc/libssl.rc.od'></code></pre>

...and so on.


### ../configure help messages

Now that we've taught redoconf which detectors we want for our project,
and run through the detectors at least once, another file gets produced as a
side effect.  This is the list of project-specific configuration options
available to `../configure`:
<pre><code lang='' src='configure.help'></code></pre>

Which now show up in the `--help` output:
```shell
$ ../configure --help
Usage: ../configure [options...] [KEY=value] [--with-key=value]

    --prefix=       Change installation prefix (usually /usr/local)
    --host=         Architecture prefix for output (eg. i686-w64-mingw32-)
    --enable-static               Link binaries statically
    --disable-shared              Do not build shared libraries
    --{dis,en}able-optimization   Disable/enable optimization for C/C++
    --{dis,en}able-debug          Disable/enable debugging flags for C/C++
    -h, --help      This help message

Project-specific flags:
    CC=...          C compiler name (cc)
    CFLAGS=...      Extra C compiler flags (eg. -O2 -g)
    CPPFLAGS=...    Extra C preprocessor flags (eg. -I... -D...)
    CXX=...         C++ compiler name (c++)
    CXXFLAGS=...    Extra C++ compiler flags (eg. -O2 -g)
    LDFLAGS=...     Extra linker options (eg. -s -static)
    LIBM=...        Extra linker options for 'libm'
    LIBS=...        Extra libraries to always link against (eg. -lsocket)
    LIBSSL=...      Extra linker options for 'libssl libcrypto'
    LINK=...        Linker name (cc)
    OPTFLAGS=...    C/C++ compiler flag overrides (eg. -g0)
```

You should include the auto-generated `configure.help` file in your source
repository, so that end users will get the right help messages the first
time they try to build your project.


### Precompiled headers

Redoconf supports the concept of precompiled headers, which can make
compilation of large C++ projects go a lot faster.  You can have one
precompiled header for C++ source files and one for C source files.

To make it work, we have to actually precompile the header, plus add some
compiler options to every other compilation to make it recognized the
precompiled headers.  We activate all that for our header, `all.hpp`,
using the `rc/all.hpp.precompiled.rc` detector, which does this:
```shell
$ redo rc/all.hpp.precompiled.rc
redo  rc/all.hpp.precompiled.rc
  CXXFLAGS_PCH_LANG += '-x
c++-header'
  CXXFLAGS += '-Winvalid-pch'
  CXXFLAGS_PCH += '-include
all.hpp'
  CXXFLAGS_PCH_FPIC += '-include
all.hpp.fpic'
  PRE_CXX_TARGETS += 'all.hpp.gch'
  PRE_CXX_TARGETS_FPIC += 'all.hpp.fpic.gch'
```

Notice that this works even though we haven't created our actual precompiled
header, `all.hpp`, yet!  That's because the detector just makes sure the
compiler can handle precompiled headers; it doesn't precompile the header
itself.  That's handled by redoconf's `default.o.od`, which does something
like `redo-ifchange $PRE_CXX_TARGETS`, where `$PRE_CXX_TARGETS` is created
by the precompilation detector above.

Here's the actual header we want to use:
<pre><code lang='c++' src='all.hpp'></code></pre>


### Compiling source files

With all that done, we're ready to actually compile a program!  Here's our
first source file:
<pre><code lang='c++' src='hello.cc'></code></pre>

and a header it needs:
<pre><code lang='c' src='ssltest.h'></code></pre>

Since we've already told redoconf what feature detectors our project needs,
redoconf can do the rest. There is a `redoconf/default.o.od` that can handle
compilation and autodependencies. We'll just ask it to produce the output.
(If you want, you can provide your own `default.o.od` which will take
precedence over the default one.  But that's rarely needed.)
```shell
$ redo hello.o
redo  hello.o
redo    cxx.precompile
redo      redoconf.h
redo        rc_vars
redo      all.hpp.gch
```

The `default.o.od` script depends on `cxx.precompile`, which does all the
things needed before compiling a C++ program (in particular, it builds all
the `$PRE_CXX_TARGETS`).  As you can see, it built `all.hpp.gch` (the
precompiled `all.hpp`) and `redoconf.h` (redoconf's equivalent of autoconf's
`config.h`).

Speaking of `redoconf.h`, here's the rest of our toy program.  This one
provides a different version of a function depending on whether libssl is
available.  It also uses redoconf to detect which header files are available
to be included:
<pre><code lang='c' src='ssltest.c'></code></pre>


### Linking

Final programs in unix are a little annoying, because they don't have file
extensions. That means redo (and redoconf) can't easily have a generalized
rule for how to build them.

In redoconf, we handle that by looking for `filename.list` whenever you ask
for `filename`.  If it exists, we assume `filename` is a binary that you
want to produce by linking together all the object files and libraries in
`filename.list`.  Furthermore, the .list file can be automatically
generated, by calling `filename.list.od`.  Here's the one for our test
program:
<pre><code lang='sh' src='hello.list.od'></code></pre>

And here's what happens:
```shell
$ redo hello
redo  hello
redo    link
redo    hello.list
redo    ssltest.o
redo      cc.precompile

$ ./hello
Hello, world!
libssl version 100020cf
```

(Notice that we had to run `cc.precompile` as a prerequisite for `ssltest.o`
here. That's because `ssltest.c` is a C program, not C++, so it has
different pre-compilation dependencies than C++. We didn't declare any
plain-C precompiled headers, but if we did, they would have happened at
this stage.)


### Cross compiling

One nice thing about redoconf is it handles cross compiling without you
having to do any extra work.  Let's try cross compiling our test program for
Windows, using the gcc-mingw32 compiler (assuming you have it installed).
If you have `wine` installed, redoconf will also try to use that for running
your produced binaries.
```shell
$ redo -j5 test
redo  test
redo    all
redo      hello
redo        link
redo          rc/_init.rc
redo          _all.rc
redo            rc/CC.rc
Trying C compiler: 'x86_64-w64-mingw32-cc'
Trying C compiler: 'x86_64-w64-mingw32-gcc'
  CPPFLAGS += '-I.'
  CC = 'x86_64-w64-mingw32-gcc'
  LINK = 'x86_64-w64-mingw32-gcc'
  LDFLAGS += '-static-libgcc
-static-libstdc++'
  ARCH = 'x86_64-w64-mingw32-'
  HAVE_CC = '1'
redo            rc/zdefs.rc
'-Wl,-z,defs' doesn't work on this platform; skipped.
redo            all.rc
redo              rc/CXX.required.rc
redo                rc/CXX.rc
Trying C++ compiler: 'x86_64-w64-mingw32-c++'
  CXX = 'x86_64-w64-mingw32-c++'
  LINK = 'x86_64-w64-mingw32-c++'
  HAVE_CXX = '1'
redo              rc/Wextra.rc
redo                rc/Wall.rc
  CPPFLAGS += '-Wall'
redo              rc/Wextra.rc (resumed)
  CPPFLAGS += '-Wextra'
redo              rc/all.hpp.precompiled.rc
  CXXFLAGS_PCH_LANG += '-x
c++-header'
  CXXFLAGS += '-Winvalid-pch'
  CXXFLAGS_PCH += '-include
all.hpp'
  CXXFLAGS_PCH_FPIC += '-include
all.hpp.fpic'
  PRE_CXX_TARGETS += 'all.hpp.gch'
  PRE_CXX_TARGETS_FPIC += 'all.hpp.fpic.gch'
redo              rc/openssl__ssl.h.rc
  HAVE_OPENSSL__SSL_H = ''
redo              rc/openssl__opensslv.h.rc
  HAVE_OPENSSL__OPENSSLV_H = ''
redo              rc/libssl.rc
redo                rc/pkg-config.rc
  PKG_CONFIG = 'pkg-config'
  HAVE_PKG_CONFIG = '1'
redo              rc/libssl.rc (resumed)
  HAVE_LIBSSL = ''
  LIBSSL = ''
redo              rc/libm.rc
  HAVE_LIBM = '1'
redo            all.rc (resumed)
  LIBS += ''
redo        hello.list
redo        hello.o
redo          compile
redo            _compile
redo          cxx.precompile
redo            redoconf.h
redo              rc_vars
redo            all.hpp.gch
redo        ssltest.o
redo          cc.precompile
redo    run
redo      rc/run.rc
redo        rc/windows.h.rc
  HAVE_WINDOWS_H = '1'
redo      rc/run.rc (resumed)
Considering RUN=''
Considering RUN='wine64'
  RUN = 'wine64'
  CAN_RUN = '1'
redo  test (resumed)
Hello, world!
libssl version 0
```

I didn't have a copy of libssl available on Windows, so `$HAVE_LIBSSL` and
`$LIBSSL` were not set.  As a result, `ssltest.o` reverted to the fallback
version of its function, and reported `libssl version 0`.  But it worked!


### Housekeeping

We want `cd out && ./configure && redo` to work, so we'll need an `all`
target.  Note that, unlike a plain redo project, redoconf projects should
use an `all.od`, because you want to `redo all` in each output directory, not
the source directory:
<pre><code lang='sh' src='all.od'></code></pre>

We should also make sure that our little program works, so let's add a `test`
target too:
<pre><code lang='sh' src='test.od'></code></pre>

Finally, let's provide a `clean.do` (not `clean.od` in this case) which
will delete any `out` and `out.*` subdirectories of the source tree.  We
could also provide a `clean.od` file for deleting files from a given
output directory, but it's usually easier to simply delete the output
directory entirely and start over.
<pre><code lang='sh' src='clean.do'></code></pre>
