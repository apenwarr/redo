% redo-ifchange(1) Redo %VERSION%
% Avery Pennarun <apenwarr@gmail.com>
% %DATE%

# NAME

redo-whichdo - show redo's search path for a .do file

# SYNOPSIS

redo-whichdo &lt;target>


# DESCRIPTION

`redo`(1) and `redo-ifchange`(1) build their targets by executing a ".do
file" script with appropriate arguments.  .do files are searched starting
from the directory containing the target, and if not found there, up the
directory tree until a match is found.

To help debugging your scripts when redo is using an unexpected .do file, or
to write advanced scripts that "proxy" from one .do file to another, you
can use `redo-whichdo` to see the exact search path that `redo` uses,
and the arguments it would use to run the .do file once found.

The output format contains lines in exactly the following order, which is
intended to be easy to parse in `sh`(1) scripts:

- Zero or more lines starting with "-", indicating .do files that were
  checked, but did not exist.  If one of these files is created, the .do
  script for your target would change.  You might
  want to call `redo-ifcreate`(1) for each of these files.

- Exactly one line starting with "+", indicating the .do file that was the
  closest match.

- Exactly one line starting with "1", indicating the first argument to the
  matching .do file.

- Exactly one line starting with "2", indicating the second argument to the
  matching .do file.

# EXAMPLE

Here's a typical search path for a source file (`x/y/a.b.o`).  Because the
filename contains two dots (.), at each level of the hierarchy, `redo` needs
to search `default.b.o.do`, `default.o.do`, and `default.do`.

        $ redo-whichdo x/y/a.b.o

        - x/y/a.b.o.do
        - x/y/default.b.o.do
        - x/y/default.o.do
        - x/y/default.do
        - x/default.b.o.do
        - x/default.o.do
        - x/default.do
        - default.b.o.do
        + default.o.do
        1 x/y/a.b.o
        2 x/y/a.b

You might use `redo-whichdo` to delegate from one .do script to another, 
using code like this:

        out=$3
        redo-whichdo "$SRCDIR/$1" | {
            x1= x2= dofile=
            ifcreate=
            while read a b; do
                case $a in
                  -)
                    ifcreate="$ifcreate $b"
                    ;;
                  +)
                    redo-ifcreate $ifcreate &&
                    redo-ifchange "$b" || exit
                    dopath="$b"
                    dodir=$(dirname "$dopath")
                    dofile=$(basename "$dopath")
                    ;;
                  1)
                    x1="$b"
                    ;;
                  2)
                    x2="$b"
                    out="$PWD/$3"
                    cd "$dodir" && . "./$dofile" "$x1" "$x2" "$out"
                    exit
                    ;;
                esac
            done
            exit 3
        }


# REDO

Part of the `redo`(1) suite.
    
# CREDITS

The original concept for `redo` was created by D. J.
Bernstein and documented on his web site
(http://cr.yp.to/redo.html).  This independent implementation
was created by Avery Pennarun and you can find its source
code at http://github.com/apenwarr/redo.


# SEE ALSO

`redo`(1), `redo-ifchange`(1), `redo-ifcreate`(1)
