# latex produces log output on stdout, which is
# not really correct.  Send it to stderr instead.
exec >&2

# We depend on both the .latex file and its .deps
# file (which lists additional dependencies)
redo-ifchange "$2.latex" "$2.deps"

# Next, we have to depend on each dependency in
# the .deps file.
cat "$2.deps" | xargs redo-ifchange

tmp="$2.tmp"
rm -rf "$tmp"
mkdir -p "$tmp"

# latex generates eg.  the table of contents by
# using a list of references ($2.aux) generated
# during its run.  The first time, the table of
# contents is empty, so we have to run again. 
# But then the table of contents is non-empty,
# which might cause page numbers to change, and
# so on.  So we have to keep re-running until it
# finally stops changing.
touch "$tmp/$2.aux.old"
ok=
for i in $(seq 5); do
    latex --halt-on-error \
        --output-directory="$tmp" \
        --recorder \
        "$2.latex" </dev/null
    if diff "$tmp/$2.aux.old" \
            "$tmp/$2.aux" >/dev/null; then
        # .aux file converged, so we're done
        ok=1
        break
    fi
    echo
    echo "$0: $2.aux changed: try again (try #$i)"
    echo
    cp "$tmp/$2.aux" "$tmp/$2.aux.old"
done

if [ "$ok" = "" ]; then
    echo "$0: fatal: $2.aux did not converge!"
    exit 10
fi

# If the newly produced .dvi disappears, we need
# to redo.
redo-ifchange "$tmp/$2.dvi"

# With --recorder, latex produces a list of files
# it used during its run.  Let's depend on all of
# them, so if they ever change, we'll redo.
grep ^INPUT "$tmp/$2.fls" |
    cut -d' ' -f2 |
    xargs redo-ifchange
