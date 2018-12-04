### Hello!

Let's start with Hello World: famously, the simplest project that does
anything interesting.  We'll write this one in C, but don't worry if
you're not a C programmer.  The focus isn't the C code itself, just to
compile it.

To play with the code on your own machine, get the [redo
source code](https://github.com/apenwarr/redo) and look in the
`docs/cookbook/hello/` directory.

### Compiling the code

First, let's create a source file that we want to compile:
<pre><code lang='c' src='hello.c'></code></pre>

Now we need a .do file to tell redo how to compile it:
<pre><code lang='sh' src='hello.do'></code></pre>

With those files in place, we can build and run the program:
```shell
$ redo hello
redo  hello

$ ./hello
Hello, world!
```

Use the `redo` command to forcibly re-run a specific rule (in this case, the
compiler).  Or, if you only want to recompile `hello` when its input
files (dependencies) have changed, use `redo-ifchange`.
```shell
$ redo hello
redo  hello

# Rebuilds, whether we need it or not
$ redo hello
redo  hello

# Does not rebuild because hello.c is unchanged
$ redo-ifchange hello

$ touch hello.c

# Notices the change to hello.c
$ redo-ifchange hello
redo  hello
```

Usually we'll want to also provide an `all.do` file.  `all` is the
default redo target when you don't specify one.
<pre><code lang='sh' src='all.do'></code></pre>

With that, now we can rebuild our project by just typing `redo`:
```shell
$ rm hello

# 'redo' runs all.do, which calls into hello.do.
$ redo
redo  all
redo    hello

# Notice that this forcibly re-runs the 'all'
# rule, but all.do calls redo-ifchange, so
# hello itself is only recompiled if its
# dependencies change.
$ redo
redo  all

$ ./hello
Hello, world!
```


### Debugging your .do scripts

If you want to see exactly which commands are being run for each step,
you can use redo's `-x` and `-v` options, which work similarly to
`sh -x` and `sh -v`.

```shell
$ rm hello

$ redo -x
redo  all
* sh -ex all.do all all all.redo2.tmp
+ redo-ifchange hello

redo    hello
* sh -ex hello.do hello hello hello.redo2.tmp
+ redo-ifchange hello.c
+ cc -o hello.redo2.tmp hello.c -Wall
redo    hello (done)

redo  all (done)
```


### Running integration tests

What about tests?  We can, of course, compile a C program that has some
unit tests.  But since our program isn't very complicated, let's write
a shell "integration test" (also known as a "black box" test) to make
sure it works as expected, without depending on implementation details:
<pre><code lang='sh' src='test.do'></code></pre>

Even if we rewrote our hello world program in python, javascript, or
ruby, that integration test would still be useful.


### Housekeeping

Traditionally, it's considered polite to include a `clean` rule that
restores your project to pristine status, so people can rebuild from
scratch:
<pre><code lang='sh' src='clean.do'></code></pre>

Some people like to include a `.gitignore` file so that git won't pester
you about files that would be cleaned up by `clean.do` anyway.  Let's add
one:
<pre><b align=center style="display: block">.gitignore</b><code>
hello
*~
.*~
</code></pre>

Congratulations!  That's all it takes to make your first redo project.

Here's what it looks like when we're done:
```shell
$ ls
all.do  clean.do  hello.c  hello.do  test.do
```

Some people think this looks a little cluttered with .do files.  But
notice one very useful feature: you can see, at a glance, exactly which
operations are possible in your project.  You can redo all, clean,
hello, or test.  Since most people downloading your project will just
want to build it, it's helpful to have the available actions so
prominently displayed.  And if they have a problem with one of the
steps, it's very obvious which file contains the script that's causing
the problem.
