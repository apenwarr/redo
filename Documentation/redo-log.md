# NAME

redo-log - display log messages from previous builds

# SYNOPSIS

redo-log [options...] [targets...]


# DESCRIPTION

When redo runs, it captures the standard error (stderr) output from the
build activity for each target, and saves it for later.  When a target is
rebuilt, the new logs replace the old logs for that target.  redo-log
prints the log output for any set of targets.

# OPTIONS

-r, --recursive
:   if the requested targets cause any dependencies to be built, recursively
    show the logs from those dependencies as well.  (And if those
    dependencies build further dependencies, also show those logs, and so on.)

-u, --unchanged
:   show messages even for dependencies that were unchanged (did not need to be
    rebuilt).  To do this, we show the logs for the *most recent* build of
    each affected dependency.  Usually this is used with `-r`.

-f, --follow
:   if a build is currently running for any of the requested targets or
    their dependencies, follow the logs (like `tail -f`) until the build
    finishes.

--no-details
:   display *only* the messages from redo itself, not the other messages
    produced by build scripts.  Generally this gives you a list of which
    targets were built, but not detailed logs, warnings, or errors.

--no-status
:   don't display the running build status at the bottom of the screen. 
    (Unless this option is specified, the status line will be enabled
    if using --follow, if stderr is a terminal.)  If stderr is *not* a
    terminal, you can force enable the status line using --status.

--no-pretty
:   display "raw" redo log lines (@@REDO events) rather than using a
    human-readable format.  The default is --pretty.

--no-color
:   when using --pretty and writing to a terminal, colorize the output to
    make results stand out more clearly.  If not writing to a terminal, you
    can use --color to force colorized output.

--debug-locks
:   print messages about acquiring, releasing, and waiting
    on locks.  Because redo can be highly parallelized,
    one instance may end up waiting for a target to be
    built by some other instance before it can continue. 
    If you suspect this is causing troubles, use this
    option to see which instance is waiting and when.
    
--debug-pids
:   add the process id of the particular redo instance to each
    output message.  This makes it easier to figure out
    which sub-instance of redo is doing what.


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
