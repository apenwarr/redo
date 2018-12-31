exec >&2
redo-ifchange whichmake

run() {
    rm -f *.out
    ./whichmake y

    rm -f *.out
    ./whichmake -j10 y

    rm -f *.out
    redo y

    rm -f *.out
    # Capture output to y.log because we know this intentionally generates
    # a scary-looking redo warning (overriding the jobserver).
    if ! redo -j10 y 2>y.log; then
        cat y.log
        exit 99
    fi
}

run
. ./wipe-redo.sh
run
