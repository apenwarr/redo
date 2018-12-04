# $1 is the target name, eg. test.txt
# $2 in the same as $1.  We'll talk about
#    that in a later example.
# $3 is the temporary output file we should
#    create.  If this script is successful,
#    redo will atomically replace $1 with $3.

if [ -e "$1.in" ]; then
    # if a .in file exists, then do some
    # text substitution.
    #
    # Remember, the user asks redo to build
    # a particular *target* name.  It's the .do
    # file's job to figure out what source file(s)
    # to use to generate the target.
    redo-ifchange "$1.in" version date
    read VERSION <version
    read DATE <date
    sed -e "s/%VERSION%/$VERSION/g" \
        -e "s/%DATE%/$DATE/g" \
        <$1.in >$3
else
    echo "$0: Fatal: don't know how to build '$1'" >&2
    exit 99
fi
