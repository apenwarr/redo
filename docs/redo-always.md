# NAME

redo-always - mark the current target as always needing to be rebuilt

# SYNOPSIS

redo-always


# DESCRIPTION

Normally redo-always is run from a .do file that has been
executed by `redo`(1).  See `redo`(1) for more details.

redo-always takes no parameters.  It simply adds an
'impossible' dependency to the current target, which
ensures that the target will always be rebuilt if anyone
runs `redo-ifchange targetname`.

Because of the way redo works, `redo-ifchange targetname`
will only rebuild `targetname` once per session.  So if
multiple targets depend on *targetname* and *targetname*
has called redo-always, only the first target will cause it
to be rebuilt.  If the build cycle completes and a new one
begins, it will be rebuilt exactly one more time.

Normally, any target that depends (directly or indirectly)
on a sub-target that has called redo-always will also
always need to rebuild, since one of its dependencies will
always be out of date.  To avoid this problem, redo-always is
usually used along with `redo-stamp`(1).


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-ifcreate`(1), `redo-ifchange`(1), `redo-stamp`(1)
