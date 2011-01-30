% redo(1) Redo %VERSION%
% Avery Pennarun <apenwarr@gmail.com>
% %DATE%

# NAME

redo-always - mark the current target as always needing to be rebuilt

# SYNOPSIS

redo-always


# DESCRIPTION

Normally redo-always is run from a .do file that has been
executed by `redo`(1).  See `redo`(1) for more details.

This is a "quoted string."

"entirely quoted"

.starting with dot

I'm a \big \\backslasher!

This **line** has _multiple_ `formats`(interspersed) *with* each _other_
and *here is a multi
line italic.*

This line has an & and a < and a >.

- "line starting with quoted"

        Here's some code
           with indentation
              yay! (a \backslash and <brackets>)
              "foo"
        
        skipped a line
           indented
           
              another skip
              
- -starting with dash

- .starting with dot

chicken

-   list item
    with more text
  
    and even more
    
    -   second list
     	-   third list

wicken

-   list 1a
-   list 1b
    -   list 2
        -   list 3

barf
          
First line
:    definition list.
     with
     multiple
     lines!
     
--item=*value*
:    a description.

`-x`
:    more stuff.  if you had a lot of text, this is what it
would look like.  It goes on and on and on.

a line with *altogether* "too much" stuff on it to realistically *make* it in a definition list
:   and yet, here we are.


# SEE ALSO

`redo`(1), `redo-ifcreate`(1), `redo-ifchange`(1), `redo-stamp`(1)
