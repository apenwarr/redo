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
can use `redo-whichdo` to see the exact search path that `redo` uses.

The output format lists potential .do files, one per line, in order of
preference, separated by newline characters, and stopping once a
matching .do file has been found.  If the return code is zero,
the last line is a .do file that actually exists; otherwise the entire
search path has been exhausted (and printed).


# EXAMPLE

Here's a typical search path for a source file (`x/y/a.b.o`).  Because the
filename contains two dots (.), at each level of the hierarchy, `redo` needs
to search `default.b.o.do`, `default.o.do`, and `default.do`.

        $ redo-whichdo x/y/a.b.o; echo $?

        x/y/a.b.o.do
        x/y/default.b.o.do
        x/y/default.o.do
        x/y/default.do
        x/default.b.o.do
        x/default.o.do
        x/default.do
        default.b.o.do
        default.o.do
        0

You might use `redo-whichdo` to delegate from one .do script to another, 
using code like the following.  This gets a little tricky because not only
are you finding a new .do file, but you have `cd` to the .do file
directory and adjust `$1` and `$2` appropriately.

        ofile=$PWD/$3
        x1=$1
        cd "$SRCDIR"
        redo-whichdo "$x1" | {
            ifcreate=
            while read dopath; do
                if [ ! -e "$dopath" ]; then
                    ifcreate="$ifcreate $dopath"
                else
                    redo-ifcreate $ifcreate
                    redo-ifchange "$dopath"

                    dofile=${dopath##*/}
                    dodir=${dopath%$dofile}

                    # Create updated $1 and $2 for the new .do file
                    x1_rel=${x1#$dodir}
                    ext=${dofile##*default}
                    if [ "$ext" != "$dofile" ]; then
                        ext=${ext%.do}
                    else
                        ext=''
                    fi
                    x2_rel=${x1#$dodir}
                    x2_rel=${x2_rel%$ext}

                    cd "$dodir"

                    set -- "$x1_rel" "$x2_rel" "$ofile"
                    . "./$dofile"
                    exit
                fi
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
