DEPS="main.o
mystr.o"
redo-ifchange $DEPS
gcc -o $3 $DEPS
