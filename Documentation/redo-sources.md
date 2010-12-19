% redo-sources(1) Redo 0.00
% Avery Pennarun <apenwarr@gmail.com>
% 2010-12-19

# NAME

redo-sources - print the list of all known redo sources

# SYNOPSIS

redo-sources


# DESCRIPTION

redo-sources prints a list of all redo *source* files that
still exist.

A source file is any file that has been listed as a
dependency (using `redo-ifchange`(1) or `redo-ifcreate`(1))
but is not itself a target.  A target is a file that
`redo`(1) can build using a .do script.

Each filename is on a separate line.  The filenames are not
guaranteed to be in any particular order.

All filenames are printed relative the current directory.
The list is not filtered in any way; it contains *all* the
source filenames from the entire project.  Remember that
the redo database may span more than just your project, so
you might need to filter the list before using it.

If you want a list of targets instead of sources, use
`redo-targets`(1) or `redo-ood`(1).


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-targets`(1), `redo-ood`(1)
