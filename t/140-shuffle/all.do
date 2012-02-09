exec >&2
. ../skip-if-minimal-do.sh

# Need to repeat this several times, on the off chance that shuffling the
# input happens to give us the same output (probability 1/factorial(9))
x=0
while [ "$x" -lt 10 ]; do
    x=$(($x + 1))
    rm -f out.log
    redo --shuffle 1.x 2.x 3.x 4.x 5.x 6.x 7.x 8.x 9.x
    sort out.log >sort.log
    if ! diff -q out.log sort.log >/dev/null; then
        exit 0
    fi
    echo "retry: #$x"
done

# still not shuffled?
exit 22
