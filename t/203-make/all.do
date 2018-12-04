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
    redo -j10 y
}

run
. ./wipe-redo.sh
run
