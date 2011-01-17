% redo-subst(1) Redo 0.00
% Andreas Krennmair <ak@synflood.at>
% 2011-01-16

# NAME

redo-subst - substitute file suffixes

# SYNOPSIS

redo-subst suffix replacement [sources...]


# DESCRIPTION

redo-subst takes a file suffix, a replacement suffix and
a list of file names on which the file suffix shall be substituted
with the replacement suffix. For every file name that ends
with the specified suffix, the suffix is removed, the
replacement suffix is appended and the resulting file name
is printed out. File names whose suffix does not match
are printed out unmodified.

# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1)
