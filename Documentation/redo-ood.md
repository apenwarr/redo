% redo-ood(1) Redo 0.00
% Avery Pennarun <apenwarr@gmail.com>
% 2010-12-19

# NAME

redo-ood - print the list of out-of-date redo targets

# SYNOPSIS

redo-ood


# DESCRIPTION

redo-ood prints a list of all redo *target* files that
exist, but are out of date.

Files that no longer exist might not be targets anymore;
you'll have to redo them for them to end up back in this
list.  (For example, if you built a file and then removed
the file and its .do file, you wouldn't want it to show up
in this list.)

If a .do script does not produce an output file (eg.
all.do, clean.do), it also does not show up in this list.

Each filename is on a separate line.  The filenames are not
guaranteed to be in any particular order.

All filenames are printed relative the current directory.
The list is not filtered in any way; it contains *all* the
target filenames from the entire project.  Remember that
the redo database may span more than just your project, so
you might need to filter the list before using it.  (A
useful heuristic might be to remove any line starting with
'../' since it often refers to a target you don't care
about.)

If you want a list of all targets, not just out-of-date
ones, use `redo-targets`(1).


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-targets`(1), `redo-sources`(1)
