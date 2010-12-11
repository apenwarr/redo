redo-ifchange all
./hello >&2
redo deltest deltest2 test.args test2.args passfailtest chdirtest \
	curse/test deps/test "space dir/test" modetest makedir2 \
	silencetest touchtest stamp/test alwaystest
