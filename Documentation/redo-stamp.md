% redo-stamp(1) Redo %VERSION%
% Avery Pennarun <apenwarr@gmail.com>
% %DATE%

# NAME

redo-stamp - detect if the current target has meaningfully changed

# SYNOPSIS

redo-stamp <$3


# DESCRIPTION

Normally, when `redo`(1) builds a target T, all the other
targets that depend on T are marked as out of date.  Even
if the rebuilt T is identical to the old one, all its
dependents need to be rebuilt.

By calling redo-stamp from your .do script, you can tell
`redo` that even though the current target is building, its
output may turn out to be unchanged.  If it hasn't, `redo`
may then be able to avoid building other targets that
depend on this target.

redo-stamp marks the current target as changed or unchanged
by comparing its stdin to the input that was provided last
time redo-stamp was called for this target.

The stamp data can be anything you want. Some possibilities
are:

- the actual target file contents:

        redo-stamp <$3
        
- a list of filenames:

        find -name '*.[ch]' | sort | redo-stamp

- the contents of a web page:

        curl http://example.org | redo-stamp

To ensure that your target gets checked every time, you
might want to use `redo-always`(1).


# DISCUSSION

While using redo-stamp is simple, the way it
works is harder to explain.  Deciding if a target is
up to date or not is the job of `redo-ifchange`(1). 
Normally, a target is considered out of date when any of its
dependencies (direct or indirect) have changed.  When that
happens, `redo-ifchange` runs the .do script for the
target, which regenerates the entire dependency list,
including rebuilding any dependencies as necessary.

Imagine that we have the following dependency chain:

    T -> X -> Y -> Z

T depends on X, which depends on Y, which depends
on Z.  Now imagine someone has changed Z.

If someone runs `redo-ifchange T`, then redo-ifchange
checks if X is up to date; to do that, it checks if Y
is up to date; and to do that, it checks whether Z is up to
date - which it isn't.  Thus, Y is not up to date, which
means X isn't, which means T isn't either, and so we need
to run T.do.  `redo-ifchange` won't directly `redo X` just
because X is dirty; it redoes T, and T.do might eventually
call `redo-ifchange X` if it needs to.

When using redo-stamp, the behaviour is different.  Let's
say Y has used redo-stamp.  In the above sequence, Y is
outdated because Z has changed.  However, we don't know yet
if Y's stamp has changed, so we don't yet know if we need
to redo X, and thus we don't know if we need to redo T.  We
can't just run `redo T`, because that could waste a lot of
time if it turns out T didn't need to be rebuilt after all.

What we do instead is note whether the *only* dependencies
of T that are out of date are 'stamped' targets.  If *any*
dependencies of T are normal, out-of-date redo targets,
then T needs to be rebuilt anyway; we don't have to do
anything special.

If the only dependency of T that has changed is Y (a
'stamped' target), then we need to `redo Y` automatically
in order to determine if T needs to be rebuilt.  This is
the only time that `redo` ever rebuilds a target that
hasn't been explicitly asked for as part of a running .do
script.


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-ifcreate`(1), `redo-ifchange`(1), `redo-always`(1)
