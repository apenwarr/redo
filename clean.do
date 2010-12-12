if [ -e .do_built ]; then
	while read x; do
		rm -f "$x"
	done <.do_built
fi
redo t/clean
rm -f *~ .*~ */*~ */.*~ *.pyc
rm -rf t/.redo
