### Containers

"Containers" became popular a few years ago with the emergence of
[Docker](https://www.docker.com/), but they are actually the result of a
long line of evolution starting with
[chroot](https://en.wikipedia.org/wiki/Chroot), a concept which dates all
the way back to 1979.  The idea of a container, or a chroot, is to run a
process or set of processes in a (more or less) isolated environment that's
separate from your main operating system.

The first iteration, chroot, only isolated the filesystem: chroot would
"change" the "root" directory (hence the name) to a subdirectory of the main
filesystem, then run a program that would see only files in that
subdirectory.  Among other things, this was used as a way to prevent rogue
programs from accidentally damaging other files on the system.  But it
wasn't particularly safe, especially because any program running with
administrator privileges could play tricks and eventually switch its root
back to the "real" root directory.  Separately from security, though, it's
sometimes interesting to install a different operating system variant in a
subdirectory, then chroot into it and run programs that require that
operating system version.  For example, if you're running the latest version
of Debian Linux, but you want to build an application that only builds
correctly on the Debian version from 5 years ago, you can install the
5-years-ago Debian files in a directory, chroot into that, and build your
application.  The main limitation is that your "host" system and your chroot
environment share the same kernel version, and rogue programs usually can
find a way to escape the chroot, so it's not useful if your inner system is
running dangerous code.

Partly in response to the limitations of chroot, "virtualization" started to
gain popularity around 2001, made famous by VMware.  (IBM mainframes had
been doing something similar for a few decades, but not many people knew how
IBM mainframes worked.) Anyway, virtualization simulates a computer's actual
hardware and lets you run a different kernel on the virtual hardware, and a
filesystem inside that hardware.  This has several advantages, including
much stricter security separation and the ability to run a different kernel
or even a different "guest" operating system than the one on the host.
Virtualization used to be pretty slow, but it's gotten faster and faster
over the years, especially with the introduction of "paravirtualization,"
where we emulate special virtual-only "hardware" that needs special drivers
in the guest, in exchange for better performance.  On Linux, the easiest
type of paravirtualization nowadays is
[kvm](https://www.linux-kvm.org/page/Main_Page) (kernel virtual machine), a
variant of [QEMU](https://www.qemu.org/).

Virtual machines provide excellent security isolation, but at the expense of
performance, since every VM instance needs to have its own kernel, drivers,
init system, terminal emulators, memory management, swap space, and so on.
In response to this, various designers decided to go back to the old
`chroot` system and start fixing the isolation limits, one by one.  The
history from here gets a bit complicated, since there are many, overlapping,
new APIs that vary between operating systems and versions.  Eventually, this
collection of features congealed into what today we call "containers," in
products like [OpenVZ](https://en.wikipedia.org/wiki/OpenVZ),
[LXC](https://en.wikipedia.org/wiki/LXC), and (most famously) Docker.

Why are we talking about all this?  Because in this tutorial, we'll use
`redo` to build and run three kinds of containers (chroot, kvm, and docker),
sharing the same app build process between all three.  redo's dependency and
parallelism management makes it easy to build multiple container types in
parallel, share code between different builds, and use different container
types (each with different tradeoffs) for different sorts of testing.


### A Hello World container

Most Docker tutorials start at the highest level of abstraction: download
someone else's container, copy your program into it, and run your program in
a container.  In the spirit of redo's low-level design, we're going to do
the opposite, starting at the very lowest level and building our way up.
The lowest level is, of course, Hello World, which we compiled (with redo of
course) in [an earlier tutorial](../hello/):
<pre><code lang='c' src='../hello/hello.c'></code></pre>

In fact, our earlier version of Hello World is a great example of redo's
safe recursion.  Instead of producing an app as part of this tutorial, we'll
just `redo-ifchange ../hello/hello` from in our new project, confident that
redo will figure out any locking, dependency, consistency, and parallelism
issues.  (This sort of thing usually doesn't work very well in `make`,
because you might get two parallel sub-instances of `make` recursing into
the `../hello` directory simultaneously, stomping on each other.)

For our first "container," we're just going to build a usable chroot
environment containing our program (`/bin/hello`) and the bare minimum
requirements of an "operating system": a shell (`/bin/sh`), an init script
(`/init`, which will just be a symlink to `/bin/hello`), and, for debugging
purposes, the all-purpose [busybox](https://busybox.net/about.html) program.

Here's a .do script that will build our simple container filesystem:
<pre><code lang='sh' src='simple.fs.do'></code></pre>

There's a catch here.  Did you see it above?  In current versions of redo,
the semantics of a .do script producing a directory as its output are
undefined.  That's because the redo authors haven't yet figured out quite
what ought to happen when a .do file creates a directory.  Or rather,
what happens *after* you create a directory?  Can people `redo-ifchange` on
a file inside that newly created directory?  What if the new directory
contains .do files?  What if you `redo-ifchange` one of the sub-files before
you `redo-ifchange` the directory that contains it, so that the sub-file's
.do doesn't exist yet?  And so on.  We don't know.  So for now, to stop you
from depending on this behaviour, we intentionally made it not work.

Instead of that, you can have a .do script that produces a *different*
directory as a side effect.  So above, `simple.fs.do` produces a directory
called `simple` when you run `redo simple.fs`.  `simple.fs` is the
(incidentally empty) output, which is managed by redo and which other
scripts can depend upon using `redo-ifchange simple.fs`.  The `simple`
directory just happens to materialize, and redo doesn't know anything about
it, which means it doesn't try to do anything about it, and you don't have
to care what redo's semantics for it might someday be.  In other words,
maybe someday we'll find a more elegant way to handle .do files that create
directories, but we won't break your old code when we do.

Okay?

All right, one more catch.  Operating systems are complicated, and there's
one more missing piece.  Our Hello World program is *dynamically linked*,
which means it depends on shared libraries elsewhere in the system.  You can
see exactly which ones by using the `ldd` command:
```shell
$ ldd ../hello/hello
	linux-vdso.so.1 (0x00007ffd1ffca000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f9ddf8fd000)
	/lib64/ld-linux-x86-64.so.2 (0x00007f9ddfe9e000)
```

If we `chroot` into our simplistic "container" and try to run `hello`, it
won't work, because those libraries aren't available to programs inside the
chroot.  That's the whole point of chroot, after all!

How do we fix it?  We get a list of the libraries with `ldd`, and then
we copy the libraries into place.

Actually, for reasons we'll address below, let's make a copy of the new
filesystem and copy the new libraries into *that*:
<pre><code lang='sh' src='libs.fs.do'></code></pre>

So now there's a directory called `simple`, which contains our program and
some helper programs, and one called `libs`, which contains all that stuff,
plus the supporting libraries.  That latter one is suitable for use with
chroot.


### Running a container with `unshare` and `chroot`

So let's run it!  We can teach redo how to start a program inside any chroot
by using a `default.do` script.  In this case, we'll use
`default.runlocal.do`.  With that file in place, when we run `redo
whatever.runlocal` (for any value of `whatever`), redo will first construct
the `whatever` directory (using `redo-ifchange whatever.fs`), and then
chroot into it and run `/init` inside.  We'll collect stdout into the redo
output (ie.  the file outside the chroot named `whatever.runlocal`).  Also,
the stderr will go to redo's build log, readable with [redo-log](/redo-log/)
or on the console at build time, and if the `/init` script returns a nonzero
exit code, so will our script.  As a result, the whole container execution
will act like a single node in our build process.  It can depend on other
things, and other things can depend on it.

Just one more thing: once upon a time, `chroot` was only available to
sysadmins, not normal users.  And it's never a good idea to run your build
scripts as root.  Luckily, Linux recently got a feature called "user
namespaces" (userns), which, among many other things, lets non-administrator
users use `chroot`.  This is a really great addition.

(Unfortunately, some people worry that user namespaces might create security
holes.  From an abundance of caution, many OSes disable user namespaces for
non-administrators by default.  So most of this script is just detecting
those situations so it can give you a useful warning.  The useful part of
the script is basically just: `unshare -r chroot "$2" /init >$3`.  Alas,
the subsequent error handling makes our script look long and complicated.)

<pre><code lang='sh' src='default.runlocal.do'></code></pre>

Speaking of error handling, the script above calls a script called
`./need.sh`, which is just a helper that prints a helpful error message and
aborts right away if the listed programs are not available to run, rather
than failing in a more complicated way.  We'll use that script more
extensively below.
<pre><code lang='sh' src='need.sh'></code></pre>

And that's it!  A super simple container!
```shell
$ redo libs.runlocal
redo  libs.runlocal
redo    libs.fs
redo      simple.fs

$ time redo libs.runlocal
redo  libs.runlocal

real	0m0.112s
user	0m0.060s
sys	0m0.024s

$ du libs
792	libs/bin
156	libs/lib64
1656	libs/lib/x86_64-linux-gnu
1660	libs/lib
3752	libs

cat libs.runlocal
Hello, world!
```

By the way, if this were a docker tutorial, it would still print "Hello,
world!" but your container would be >100 megabytes instead of 3.7 megabytes,
and it would have taken at least a couple of seconds to start instead of
0.11 seconds.  But we'll get to that later.  First, now that we have a
container, let's do more stuff with it!

### Running a container with `kvm` and `initrd`

Now you've seen chroot in action, but we can run almost the same container
in `kvm` (kernel virtual machine) instead, with even greater isolation.
`kvm` only runs on Linux, so for this step you'll need a Linux machine. And
for our example, we'll just have it run exactly the same kernel you're
already using, although kvm has the ability to use whatever kernel you want.
(You could even build a kernel as part of your redo project, redo-ifchange
it, and then run it with kvm.  But we're not going to do that.)

Besides a kernel, kvm needs an "initial ramdisk", which is where it'll get
its filesystem.  (kvm can't exactly access your normal filesystem,
because it's emulating hardware, and there's no such thing as "filesystem
hardware." There are tools like the [9p
filesystem](https://www.kernel.org/doc/Documentation/filesystems/9p.txt)
that make this easier, but it's not available in all kernel builds, so we'll
avoid it for now.)

"Initial ramdisk" (initrd) sounds fancy, but it's actually just a tarball
(technically, a [cpio](https://en.wikipedia.org/wiki/Cpio) archive) that the
kernel extracts into a ramdisk at boot time.  Since we already have the
files, making the tarball is easy:
<pre><code lang='sh' src='default.initrd.do'></code></pre>

(Ignore that `try_fakeroot.sh` thing for now.  We'll get to it a bit further
down.  In our `simple.fs` example, it's a no-op anyway.)

The main thing you need to know is that, unlike tar, cpio takes a list of
files on stdin instead of on the command line, and it doesn't recurse
automatically (so if you give it a directory name, it'll store an entry for
that directory, but not its contents, unless you also provide a list of its
contents).  This gives us a lot of power, which we'll use later.  For now
we're just doing basically `find | cpio -o`, which takes all the files and
directories and puts them in a cpio archive file.
```shell
$ redo libs.initrd
redo  libs.initrd
5163 blocks
1 block

$ cpio -t <libs.initrd
.
bin
bin/hello
bin/busybox
bin/sh
lib64
lib64/ld-linux-x86-64.so.2
lib
lib/x86_64-linux-gnu
lib/x86_64-linux-gnu/libc.so.6
init
7444 blocks
```

`default.initrd.do` also appends another file, `rdinit` (the "ram disk init"
script), which is the first thing the kvm Linux kernel will execute after
booting.  We use this script to set up a useful environment for our
container's `/init` script to run in - notably, it has to write its stdout
to some virtual hardware device, so redo can capture it, and it has to save
its exit code somewhere, so redo knows whether it suceeded or not.  Here's a
simple `rdinit` script that should work with any container we want to run
using this technique:
<pre><code lang='sh' src='rdinit'></code></pre>

Configuring a virtual machine can get a little complicated, and there are a
million things we might want to do.  One of the most important is setting
the size of the ramdisk needed for the initrd.  Current Linux versions limit
the initrd to half the available RAM in the (virtual) machine, so to be
safe, we'll make sure to configure kvm to provide at least 3x as much RAM as
the size of the initrd.  Here's a simple script to calculate that:
<pre><code lang='sh' src='memcalc.py'></code></pre>

With all those pieces in place, actually executing the kvm is pretty
painless.  Notice in particular the three serial ports we create: one for
the console (stderr), one for the output (stdout), and one for the exit
code:
<pre><code lang='sh' src='default.runkvm.do'></code></pre>

And it works!
```shell
$ redo libs.runkvm
redo  libs.runkvm
redo    libs.initrd
5163 blocks
1 block
libs: kvm memory required: 70M
[    0.306682] reboot: Power down
ok.

$ time redo libs.runkvm
redo  libs.runkvm
libs: kvm memory required: 70M
[    0.295139] reboot: Power down
ok.

real	0m0.887s
user	0m0.748s
sys	0m0.112s

$ cat libs.runkvm
Hello, world!
```

Virtual machines have come a long way since 1999: we managed to build an
initrd, boot kvm, run our program, and shut down in only 0.9 seconds.  It
could probably go even faster if we used a custom-built kernel with no
unnecessary drivers.


### A real Docker container

Okay, that was fun, but nobody in real life cares about all these fast,
small, efficient isolation systems that are possible for mortals to
understand, right?  We were promised a **Container System**, and a container
system has daemons, and authorization, and quotas, and random delays, and
some kind of Hub where I can download (and partially deduplicate) someone
else's multi-gigabyte Hello World images that are built in a highly
sophisticated enterprise-ready collaborative construction process.  Come on,
tell me, can redo do **that**?

Of course!  But we're going to get there the long way.

First, let's use the big heavy Container System with daemons and delays to
run our existing tiny understandable container.  After that, we'll show how
to build a huge incomprehensible container that does the same thing, so your
co-workers will think you're normal.

#### Docker and layers

Normal people build their Docker containers using a
[Dockerfile](https://docs.docker.com/engine/reference/builder/).  A
Dockerfile is sort of like a non-recursive redo, or maybe a Makefile, except
that it runs linearly, without the concept of dependencies or
parallelization.  In that sense, I guess it's more like an IBM mainframe job
control script from 1970.  It even has KEYWORDS in ALL CAPS, just like 1970.

Dockerfiles do provide one really cool innovation over IBM job control
scripts, which is that they cache intermediate results so you don't have to
regenerate it every time.  Basically, every step in a Dockerfile copies a
container, modifies it slightly, and saves the result for use in the next
step.  If you modify step 17 and re-run the Dockerfile, it can just start
with the container produced by step 16, rather than going all the way back
to step 1.  This works pretty well, although it's a bit expensive to start
and stop a container at each build step, and it's unclear when and how
interim containers are expunged from the cache later.  And some of your
build steps are "install the operating system" and "install the compiler",
so each step produces a larger and larger container.  A very common mistake
among Docker users is to leave a bunch of intermediate files (source code,
compilers, packages, etc) installed in the output container, bloating it up
far beyond what's actually needed to run the final application.

Spoiler: we're not going to do it that way.

Instead, let's use redo to try to get the same Dockerfile advantages
(multi-stage cache; cheap incremental rebuilds) without the disadvantages
(launching and unlaunching containers; mixing our build environment with our
final output).

To understand how we'll do this, we need to talk about
[Layers](https://medium.com/@jessgreb01/digging-into-docker-layers-c22f948ed612).
Unlike our kvm initrd from earlier, a Docker image is not just a single
tarball; it's a sequence of tarballs, each containing the set of files
changed at each step of the build process.  This layering system is how
Docker's caching and incremental update system works: if I incrementally
build an image starting from step 17, based on the pre-existing output from
step 16, then the final image can just re-use layers 1..16 and provide new
layers 17..n.  Usually, the first few layers (install the operating system,
install the compilers, etc) are the biggest ones, so this means a new
version of an image takes very little space to store or transfer to a system
that already has the old one.

The inside of a docker image looks like this:
```shell
 $ tar -tf test.image
ae5419fd49e39e4dc0baab438925c1c6e4417c296a8b629fef5ea93aa6ea481c/
ae5419fd49e39e4dc0baab438925c1c6e4417c296a8b629fef5ea93aa6ea481c/VERSION
ae5419fd49e39e4dc0baab438925c1c6e4417c296a8b629fef5ea93aa6ea481c/json
ae5419fd49e39e4dc0baab438925c1c6e4417c296a8b629fef5ea93aa6ea481c/layer.tar
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/VERSION
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/json
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/layer.tar
```

We could use redo to build a Docker image by simply making a single
`layer.tar` of the filesystem (like we did with initrd), adding a VERSION
and json file, and putting those three things into an outer taball.  But if
we want a system that works as well as a Dockerfile, we'll have to make use
of multiple layers.

Our `simple` container is already pretty tiny by container standards - 2.6MB
- but it's still a bit wasteful.  Most of that space turns out to be from
the dynamic libraries we imported from the host OS.  These libraries don't
change when we change Hello World!  They belong in their own layer.

Up above, in preparation for this moment, we created `libs.fs.do` to build a
separate filesystem, rather than adding the libraries inside
`simple.fs.do`, which would have been easier.  Now we can make each of those
filesystems its own layer.

There's one more complication: we did things a bit backwards.  In a
Dockerfile, you install the libraries first, and then you install your
application.  When you replace your application, you replace only the
topmost layer.  We did it the other way around: we installed our
application and some debugging tools, then detected which libraries they
need and added a layer on top.  The most recent versions of Docker, 1.10 and
above, are more efficient about handling layers changing in the middle of
the stack, but not everyone is using newer Docker versions yet, so let's try
to make things efficient for older Docker versions too.

Luckily, since we're starting from first principles, in redo we can do
anything we want.  We have to generate a tarball for each layer anyway, so
we can decide what goes into each layer and then we can put those layers in
whatever sequence we want.

Let's start simple.  A layer is just a tarball made of a set of files
(again, ignore the `try_fakeroot` stuff for now):
<pre><code lang='sh' src='default.layer.do'></code></pre>

The magic, of course, is in deciding which files go into which layers.  In
the script above, that's provided in the .list file corresponding to each
layer.  The .list file is produced by `default.list.do`:
<pre><code lang='sh' src='default.list.do'></code></pre>

This requires a bit of explanation.  First of all, you probably haven't seen
the very old, but little-known `comm` program before.  It's often described
as "compare two sorted files" or "show common lines between two files."  But
it actually does more than just showing common lines: it can show the lines
that are only in file #1, or only in file #2, or in both files.  `comm -1
-3` *suppresses* the output of lines that are only in #1 or that are in
both, so that it will print only the lines in the second file.

If we want to make a `libs.layer` that contains only the files that are
*not* in `simple`, then we can use `comm -1 -3` to compare `simple` with
`libs`.

Now, this script is supposed to be able to construct the file list for any
layer.  To do that, it has to know what parent to compare each layer
against.  We call that the "diffbase", and for layers that are based on
other layers, we put the name of the parent layer in its diffbase file:
<pre><code lang='sh' src='libs.diffbase'></code></pre>

(If there's no diffbase, then we use /dev/null as the diffbase.  Because if
file #1 is empty, then *all* the lines are only in file #2, which is exactly
what we want.)

There's just one more wrinkle: if we just compare lists of files, then we'll
detect newly-added files, but we won't detect *modified* files.  To fix
this, we augment the file list with file checksums before the comparison
(using `fileids.py`), then strip the checksums back out in
`default.layer.do` before sending the resulting list to `cpio`.

The augmented file list looks like this:
```shell
$ cat simple.list
. 0040755-0-0-0
./bin 0040755-0-0-0
./bin/busybox 0100755-0-0-ba34fb34865ba36fb9655e724266364f36155c93326b6b73f4e3d516f51f6fb2
./bin/hello 0100755-0-0-22e4d2865e654f830f6bfc146e170846dde15185be675db4e9cd987cb02afa78
./bin/sh 0100755-0-0-e803088e7938b328b0511957dcd0dd7b5600ec1940010c64dbd3814e3d75495f
./init 0120777-0-0-14bdc0fb069623c05620fc62589fe1f52ee6fb67a34deb447bf6f1f7e881f32a
```

(Side note: the augmentation needs to be added at the end of the line, not
the beginning so that the file list is still sorted afterwards.  `comm` only
works correctly if both input files are sorted.)

The script for augmenting the file list is fairly simple.  It just reads a
list of filenames on stdin, checksums those files, and writes the augmented
list on stdout:
<pre><code lang='sh' src='fileids.py'></code></pre>

Just one more thing!  Docker (before 1.10) deduplicates images by detecting
that they contain identical layers.  When using a Dockerfile, the layers are
named automatically using random 256-bit numbers (UUIDs).  Since Dockerfiles
usually don't regenerate earlier layers, the UUIDs of those earlier layers
won't change, so future images will contain layers with known UUIDs, so
Docker doesn't need to deduplicate them.

We don't want to rely on never rebuilding layers.  Instead, we'll adopt a
technique from newer Docker versions (post 1.10): we'll name layers after a
checksum of their contents.  Now, we don't want to actually checksum the
`whatever.layer` file, because it turns out that tarballs contain a bunch of
irrelevant details, like inode numbers and
[mtimes](https://apenwarr.ca/log/20181113), so they'll have a different
checksum every time they're built.  Instead, we'll make a digest of the
`whatever.list` file, which conveniently already has a checksum of each
file's contents, plus the interesting subset of the file's attributes.

Docker expects 256-bit layer names, so we might normally generate a sha256
digest using the `sha256sum` program, but that's not available on all
platforms.  Let's write a python script to do the job instead.  To make it
interesting, let's write it as a .do file, so we can generate the sha256 of
`anything` by asking for `redo-ifchange anything.sha256`.  This is a good
example of how in redo, .do files can be written in any scripting language,
not just sh.
<pre><code lang='sh' src='default.sha256.do'></code></pre>

Let's test it out:
```shell
$ redo simple.list.sha256
redo  simple.list.sha256
redo    simple.list

$ cat simple.list.sha256
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145

$ rm -rf simple

$ redo simple.list.sha256
redo  simple.list.sha256
redo    simple.list
redo      simple.fs

$ cat simple.list.sha256
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145
```

Consistent layer id across rebuilds!  Perfect.

#### Combining layers: building a Docker image

We're almost there.  Now that we can produce a tarball for each layer, we
have to produce the final tarball that contains all the layers in the right
order.  For backward compatibility with older Docker versions, we also need
to produce a json "manifest" for each layer.  In those old versions, each
layer was also its own container, so it needed to have all the same
attributes as a container, including a default program to run, list of open
ports, and so on.  We're never going to use those values except for the
topmost layer, but they have to be there, so let's just auto-generate them.
Here's the script for customizing each layer's json file from a template:
<pre><code lang='sh' src='dockjson.py'></code></pre>

And here's the empty template:
<pre><code lang='sh' src='template.json'></code></pre>

Now we just need to generate all the layers in a subdirectory, and tar them
together:
<pre><code lang='sh' src='default.image.do'></code></pre>

This requires a list of layers for each image we might want to create.
Here's the list of two layers for our `simple` container:
<pre><code lang='sh' src='simple.image.layers'></code></pre>

Finally, some people like to compress their Docker images for transport or
uploading to a repository.  Here's a nice .do script that can produce the
.gz compressed version of any file:
<pre><code lang='sh' src='default.gz.do'></code></pre>

Notice the use of `--rsyncable`.  Very few people seem to know about this
gzip option, but it's immensely handy.  Normally, if a few bytes change
early in a file, it completely changes gzip's output for all future bytes,
which means that incremental copying of new versions of a file (eg. using
`rsync`) is very inefficient.  With `--rsyncable`, gzip does a bit of extra
work to make sure that small changes in one part of a file don't affect the
gzipped bytes later in the file, so an updated container will be able to
transfer a minimal number of bytes, even if you compress it.

Let's try it out!
```shell
$ redo simple.image.gz
redo  simple.image.gz
redo    simple.image
redo      libs.list.sha256
redo        libs.list
redo          simple.list
redo      libs.layer
3607 blocks
redo      simple.list.sha256
redo      simple.layer
1569 blocks
layer: b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95 libs
layer: 4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145 simple

flow:~/src/redo/docs/cookbook/container $ tar -tf simple.image.gz
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145/
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145/VERSION
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145/json
4d1fda9f598191a4bc281e5f6ac9c27493dbc8dd318e93a28b8a392a7105c145/layer.tar
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/VERSION
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/json
b65ae6e742f8946fdc3fbdccb326378162641f540e606d56e1e638c7988a5b95/layer.tar
```

In the above, notice how we build libs.layer first and simple.layer second,
because that's the order of the layers in `simple.image.layers`.  But to
produce `libs.list` we need to compare the file list against `simple.list`,
so it declares a dependency on `simple.list`.

The final `simple.image` tarball then includes the layers in *reverse* order
(topmost to bottommost), because that's how Docker does it.  The id of the
resulting docker image is the id of the topmost layer, in this case
4d1fda9f.

#### Loading and running a Docker image

Phew!  Okay, we finally have a completed Docker image in the format Docker
expects, and we didn't have to execute even one Dockerfile.  Incidentally,
that means all of the above steps could run without having Docker installed,
and without having any permissions to talk to the local Docker daemon.
That's a pretty big improvement (in security and manageability) over running
a Dockerfile.

The next step is to load the image into Docker, which is easy:
<pre><code lang='sh' src='default.load.do'></code></pre>

And finally, we can ask Docker to run our image, and capture its output like
we did, so long ago, in `default.runlocal.do` and `default.runkvm.do`:
<pre><code lang='sh' src='default.rundocker.do'></code></pre>

The result is almost disappointing in its apparent simplicity:
```shell
$ time redo simple.rundocker
redo  simple.rundocker
redo    simple.load

real	0m2.688s
user	0m0.068s
sys	0m0.036s

$ cat simple.rundocker
Hello, world!
```

Notice that, for some reason, Docker takes 2.7s to load, launch and run our
tiny container.  That's about 3x as long as it takes to boot and run a kvm
virtual machine up above with exactly the same files.  This is kind of
weird, since containers are supposed to be much more lightweight than
virtual machines.  I'm sure there's a very interesting explanation for this
phenomenon somewhere.  For now, notice that you might save a lot of time by
initially testing your containers using `default.runlocal` (0.11 seconds)
instead of Docker (2.7 seconds), even if you intend to eventally deploy them
in Docker.


### A Debian-based container

We're not done yet!  We've built and run a Docker container the hard way,
but we haven't built and run an **unnecessarily wastefully huge** Docker
container the hard way.  Let's do that next, by installing Debian in a
chroot, then packaging it up into a container.

As we do that, we'll recycle almost all the redo infrastructure we built
earlier while creating our `simple` container.

#### Interlude: Fakeroot

It's finally time to talk about that mysterious `try_fakeroot.sh` script
that showed up a few times earlier.  It looks like this:
<pre><code lang='sh' src='try_fakeroot.sh'></code></pre>

[fakeroot](https://wiki.debian.org/FakeRoot) is a tool, originally developed
for the Debian project, that convinces your programs that they are running
as root, without actually running them as root.  This is mainly so that they
can pretend to chown() files, without actually introducing security holes on
the host operating system.  Debian uses this when building packages: they
compile the source, start fakeroot, install to a fakeroot directory,
make a tarball of that directory, then exit fakeroot.  The tarball then
contains the permissions they want.

Normally, fakeroot forgets all its simulated file ownership and permissions
whenever it exits.  However, it has `-s` (save) and `-i` (input) options for
saving the permissions to a file and reloading the permissions from that
file, respectively.

As we build our container layers, we need redo to continually enter
fakeroot, do some stuff, and exit it again.  The `try_fakeroot.sh` script is
a helper to make that easier.

#### Debootstrap

The next Debian tool we should look at is
[debootstrap](https://wiki.debian.org/Debootstrap).  This handy program
downloads and extracts the (supposedly) minimal packages necessary to build
an operational Debian system in a chroot-ready subdirectory.  Nice!

In order for debootstrap to work without being an administrator - and you
should not run your build system as root - we'll use fakeroot to let it
install all those packages.

Unfortunately, debootstrap is rather slow, for two reasons:

1. It has to download a bunch of things.
2. It has to install all those things.

And after debootstrap has run, all we have is a Debian system, which by
itself isn't a very interesting container.  (You usually want your container
to have an app so it does something specific.)

Does this sound familiar?  It sounds like a perfect candidate for Docker
layers.  Let's make three layers:

1. Download the packages.
2. Install the packages.
3. Install an app.

Here's step one:
<pre><code lang='sh' src='debdownload.fs.do'></code></pre>

On top of that layer, we run the install process:
<pre><code lang='sh' src='debootstrap.fs.do'></code></pre>

Since both steps run debootstrap and we might want to customize the set of
packages to download+install, we'll put the debootstrap options in their own
shared file:
<pre><code lang='sh' src='debootstrap.options'></code></pre>

And finally, we'll produce our "application" layer, which in this case is
just a shell script that counts then number of installed Debian packages:
<pre><code lang='sh' src='debian.fs.do'></code></pre>


#### Building the Debian container

Now that we have the three filesystems, let's actually generate the Docker
layers.  But with a catch: we won't actually include the layer for step 1,
since all those package files will never be needed again.  (Similarly, if we
were installing a compiler - and perhaps redo! - in the container so we
could build our application in a controlled environment, we might want to
omit the "install compiler" layers from the final product.)

So we list just two layers:
<pre><code lang='sh' src='debian.image.layers'></code></pre>

And the 'debian' layer's diffbase is `debootstrap`, so we don't include the
same files twice:
<pre><code lang='sh' src='debian.diffbase'></code></pre>


#### Running the Debian container

This part is easy.  All the parts are already in place.  We'll just run
the existing `default.rundocker.do`:
```shell
$ time redo debian.rundocker
redo  debian.rundocker
redo    debian.load
redo      debian.image
redo        debian.list.sha256
redo          debian.list
redo        debian.layer
12 blocks
layer: a542b5976e1329b7664d79041d982ec3d9f7949daddd73357fde17465891d51d debootstrap
layer: d5ded4835f8636fcf01f6ccad32125aaa1fe9e1827f48f64215b14066a50b9a7 debian

real	0m7.313s
user	0m0.632s
sys	0m0.300s

$ cat debian.rundocker
82
```

It works!  Apparently there are 82 Debian packages installed.  It took 7.3
seconds to load and run the docker image though, probably because it had to
transfer the full contents of those 82 packages over a socket to the docker
server, probably for security reasons, rather than just reading the files
straight from disk.  Luckily, our chroot and kvm scripts also still work:
```shell
$ time redo debian.runlocal
redo  debian.runlocal

real	0m0.084s
user	0m0.052s
sys	0m0.004s

$ cat debian.runlocal
82

$ time redo debian.runkvm
redo  debian.runkvm
redo    debian.initrd
193690 blocks
1 block
debian: kvm memory required: 346M
[    0.375365] reboot: Power down
ok.

real	0m3.445s
user	0m1.008s
sys	0m0.644s

$ cat debian.runkvm
82
```

#### Testing and housekeeping

Let's finish up by providing the usual boilerplate.  First, an `all.do` that
builds, runs, and tests all the images on all the container platforms. 
This isn't a production build system, it's a subdirectory of the redo
package, so we'll skip softly, with a warning, if any of the components are
missing or nonfunctional.  If you were doing this in a "real" system, you
could just let it abort when something is missing.
<pre><code lang='sh' src='all.do'></code></pre>

And here's a `redo clean` script that gets rid of (most of) the files
produced by the build.  We say "most of" the files, because actually we
intentionally don't delete the debdownload and debootstrap directories. 
Those take a really long time to build, and redo knows to rebuild them if
their dependencies (or .do files) change anyway.  So instead of throwing
away their content on 'redo clean', we'll keep it around.
<pre><code lang='sh' src='clean.do'></code></pre>

Still, we want a script that properly cleans up everything, so let's have
`redo xclean` (short for "extra clean") wipe out the last remaining
files:
<pre><code lang='sh' src='xclean.do'></code></pre>
