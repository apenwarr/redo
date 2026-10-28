. ../skip-if-minimal-do.sh

rm -rf outer
mkdir -p outer/inner/.redo
mkdir -p outer/.redo

echo 'echo "$REDO_BASE"' >outer/inner/test.do

(
    cd outer/inner
    env -i PATH="$PATH" REDO="$REDO" ${REDO:-redo} --no-log test
    base=$(cat test)
    expected=$(pwd -P)
    if [ "$base" != "$expected" ]; then
        echo "Error: REDO_BASE was '$base', expected '$expected'" >&2
        exit 1
    fi
)

rm -rf outer
