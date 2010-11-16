if [ -e "$1$2.a" -o -e "default$2.a" ]; then
	redo-ifchange "$1$2.a"
	echo a-to-b
	cat "$1$2.a"
else
	redo-ifchange "$1$2.b"
	echo b-to-b
	cat "$1$2.b"
fi
./sleep 1.1
