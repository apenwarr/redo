if [ -e .do_built ]; then
	while read x; do
		rm -f "$x"
	done <.do_built
fi
[ -z "$DO_BUILT" ] && rm -rf .do_built .do_built.dir
redo t/clean Documentation/clean
rm -f *~ .*~ */*~ */.*~ *.pyc install.wrapper
rm -rf t/.redo
find . -name '*.tmp' -exec rm -fv {} \;
