### A LaTeX typesetting example

[LaTeX](https://www.latex-project.org/) is a typesetting system that's
especially popular in academia.  Among other things, it lets you produce
postscript and pdf files from a set of (mostly text) input files.

LaTeX documents often include images and charts.  In our example, we'll show
how to auto-generate a chart for inclusion using an [R script with
ggplot2](https://ggplot2.tidyverse.org/).

To play with this code on your own machine, get the [redo
source code](https://github.com/apenwarr/redo) and look in the
`docs/cookbook/latex/` directory.


### Generating a plot from an R script

First, let's tell redo how to generate our chart.  We'll use
the R language, and ask it to plot some of its sample data (the mpg, "miles
per gallon" data set) and save it to an eps (encapsulated postscript) file. 
eps files are usually a good format for LaTeX embedded images, because they
scale to any printer or display resolution.

First, let's make an R script that generates a plot:
<pre><code lang='r' src='mpg.R'></code></pre>

And then a .do file to tie that into redo:
<pre><code lang='sh' src='mpg.eps.do'></code></pre>

We can build and view the image:
```shell
$ redo mpg.eps 
redo  mpg.eps

# View the file on Linux
$ evince mpg.eps

# View the file on MacOS
$ open mpg.eps
```


### Running the LaTeX processor

Here's the first draft of our very important scientific paper:
<pre><code lang='tex' src='paper.latex'></code></pre>

Notice how it refers to the chart from above, `mpg.eps`, and a text file,
`discovery.txt`.  Let's create the latter as a static file.
<pre><code lang='tex' src='discovery.txt'></code></pre>

With all the parts of our document in places, we can now compile it directly
using `pdflatex`:
```shell
$ pdflatex paper.latex 
This is pdfTeX, Version 3.14159265-2.6-1.40.17 (TeX Live 2016/Debian) (preloaded format=pdflatex)
 restricted \write18 enabled.
entering extended mode
...[a lot of unnecessary diagnostic messages]...
Output written on paper.pdf (2 pages, 68257 bytes).
Transcript written on paper.log.
```

But this has a few problems.  First of all, it doesn't understand
dependencies; if `mpg.R` changes, it won't know to rebuild `mpg.eps`. 
Secondly, the TeX/LaTeX toolchain has an idiosyncracy that means you might
have to rebuild your document more than once.  In our example, we generate a
table of contents, but it ends up getting generated *before* processing the
rest of the content in the document, so it's initially blank.  As it
continues, LaTeX produces a file called `paper.aux` with a list of the
references needed by the table of contents, and their page numbers.  If we
run LaTeX over again, it'll use that to build a proper of table of contents.

Of course, life is not necessarily so easy.  Once the table of contents
isn't blank, it might start to push content onto the next page.  This will
change all the page numbers!  So we'd have to do it one more time.  And that
might lead to even more subtle problems, like a reference to page 99
changing to page 100, which pushes a word onto the next page, which changes
some other page number, and so on.  Thus, we need a script that will keep
looping, re-running LaTeX until `paper.aux` stabilizes.

The whole script we'll use is below.  Instead of running `pdflatex`
directly, we'll use the regular `latex` command, which produces a .dvi
(DeVice Independent) intermediate file which we can later turn into a pdf or
ps file.

LaTeX produces a bunch of clutter files (like `paper.aux`) that can be used
in future runs, but which also make its execution nondeterministic.  To
avoid that problem, we tell it to use a temporary `--output-directory` that
we delete and recreate before each build (although we might need to run
`latex` multiple times in one build, to get `paper.aux` to converge).
<pre><code lang='sh' src='default.runtex.do'></code></pre>


### Virtual targets, side effects, and multiple outputs

Why did we call our script `default.runtex.do`?  Why not `default.pdf.do` or
`default.dvi.do`, depending what kind of file we ask LaTeX to produce?

The problem is that the `latex` command actually produces several
files in that temporary directory, and we might want to keep them around. 
If we name our .do file after only *one* of those outputs, things get messy.

The biggest problem is that redo requires a .do file to write its output to
$3 (or stdout), so that it can guarantee the output gets replaced
atomically.  When there is more than one output, at most one file can
be sent to $3; how do you choose which one?  Even worse, some programs don't
even have the ability to choose the output filename; for an input of
`paper.latex`, the `latex` command just writes a bunch of files named
`paper.*` directly.  You can't ask it to put just one of them in $3.

The easiest way to handle this situation in redo is to use a "virtual
target", which is a target name that doesn't actually get created has a file,
and has only side effects.  You've seen these before: when we use `all.do`
or `clean.do`, we don't expect to produce a file named `all` or `clean`.  We
expect redo to run a collection of other commands.  In `make`, these are
sometimes called ".PHONY rules" because of the way they are declared in a
`Makefile`.  But the rules aren't phony, they really are executed; they just
don't produce output.  So in redo we call them "virtual."

When we `redo paper.runtex`, it builds our virtual target.  There is no
`paper.runtex` file or directory generated.  But as a side effect, a
directory named `paper.tmp` is created.

(Side note: it's tempting to name the directory the same as the target.  So
we could have a `paper.runtex` directory instead of `paper.tmp`.  This is
not inherently a bad idea, but currently redo behaviour is undefined if you
redo-ifchange a directory.  Directories are weird.  If one file in that
directory disappears, does that mean you "modified" the output by hand? 
What if two redo targets modify the same directory?  Should we require
scripts to only atomically replace an entire output directory via $3?  And
so on.  We might carefully define this behaviour eventually, but for now,
it's better to use a separate directory name and avoid the undefined
behaviour.)


### Depending on side effects produced by virtual targets

Next, we want to produce .pdf and .ps files from the collection of files
produced by the `latex` command, particularly `paper.tmp/paper.dvi`.  To do
that, we have to bring our files back from the "virtual target" world into
the real world.

Depending on virtual targets is easy; we'll just
`redo-ifchange paper.runtex`.  Then we want to materialize `paper.dvi` from
the temporary files in `paper.tmp/paper.dvi`, which we can do with an
efficient [hardlink](https://en.wikipedia.org/wiki/Hard_link) (rather than
making an unnecessary copy), like this:
<pre><code lang='sh' src='default.dvi.do'></code></pre>

Notice that we *don't* do `redo-ifchange paper.tmp/paper.dvi`.  That's
because redo has no knowledge of that file.  If you ask redo to build that
file for you, it doesn't know how to do it.  You have to ask for
`paper.runtex`, which you know - but redo doesn't know - will produce the
input file you want.  Then you can safely use it.

Once we have a .do file that produces the "real" (non-virtual,
non-side-effect) `paper.dvi` file, however, it's safe to depend directly on
it.  Let's use that to produce our .ps and .pdf outputs:
<pre><code lang='sh' src='default.ps.do'></code></pre>
<pre><code lang='sh' src='default.pdf.do'></code></pre>

(As above, we include `exec >&2` lines because LaTeX tools incorrectly write
their log messages to stdout.  We need to redirect it all to stderr.  That
way [redo-log](../../redo-log) can handle all the log output appropriately.)


### Explicit dependencies

We've made a generalized script, `default.runtex.do`, that can compile any
.latex file and produce a .tmp directory with its output.  But that's not
quite enough: different .latex files might have extra dependencies that need
to exist *before* the compilation can continue.  In our case, we need the
auto-generated `mpg.eps` that we discussed above.

To make that work, `default.runtex.do` looks for a .deps file with the same
name as the .latex file being processed.  It contains just a list of extra
dependencies that need to be built.  Here's ours:
<pre><code src='paper.deps'></code></pre>

You can use this same ".deps" technique in various different places in redo. 
For example, you could have a default.do that can link a C program from any
set of .o files.  To specify the right set of .o files for target `X`,
default.do might look in an `X.deps` or `X.list` file.  If you later want to
get even fancier, you could make an `X.deps.do` that programmatically
generates the list of dependencies; for example, it might include one set of
files on win32 platforms and a different set on unix platforms.


### Autodependencies

Our `paper.latex` file actually includes two files: `mpg.eps`, which we
explicitly depended upon above, and `discovery.txt`, which we didn't.  The
latter is a static source file, so we can let redo discover it
automatically, based on the set of files that LaTeX opens while it runs. 
The `latex` command has a `--record` option to do this; it produces a file
called `paper.tmp/paper.fls` (.fls is short for "File LiSt").

One of redo's best features is that you can declare dependencies *after*
you've done your build steps, when you have the best knowledge of which
files were actually needed.  That's why in `default.runtex.do`, we parse the
.fls file and then redo-ifchange on its contents right at the end.

(This brings up a rather subtle point about how redo works.  When you run
redo-ifchange, redo adds to the list of files which, if they change, mean
your target needs to be rebuilt.  But unlike make, redo will not actually
rebuild those files merely because they're listed as a dependency; it just
knows to rebuild your target, which means to run your .do file, which will
run redo-ifchange *again* if it still needs those input files to be fresh.

This avoids an annoying problem in `make` where you can teach it about
which .h files your C program depended on last time, but if you change
A.c to no longer include X.h, and then delete X.h, make might complain
that X.h is missing, because A.c depended on it *last time*.  redo will
simply notice that since X.h is missing, A.c needs to be recompiled, and let
your compilation .do script report an error, or not.)

Anyway, this feature catches not just our `discovery.txt` dependency, but
also the implicit dependencies on various LaTeX template and font files, and
so on.  If any of those change, our LaTeX file needs to be rebuilt.
```shell
$ redo --no-detail paper.pdf
redo  paper.pdf
redo    paper.dvi
redo      paper.runtex
redo        mpg.eps
                                                                                            
$ redo --no-detail paper.pdf
redo  paper.pdf

$ touch discovery.txt 

$ redo --no-detail paper.pdf
redo  paper.pdf
redo    paper.dvi
redo      paper.runtex

$ redo --no-detail paper.pdf
redo  paper.pdf
```


### Housekeeping

As usual, to polish up our project, let's create an `all.do` and
`clean.do`.

Because this project is included in the redo source and we don't want redo
to fail to build just because you don't have LaTeX or R installed, we'll
have `all.do` quit politely if the necessary tools are missing.
<pre><code lang='sh' src='all.do'></code></pre>
<pre><code lang='sh' src='clean.do'></code></pre>
