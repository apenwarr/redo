redo-ifchange t/c.c t/all
echo >&2
./wvtestrun "$REDO" runtests >&2
