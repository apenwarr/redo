DEPS="main.o
mystr.o"
redo-ifchange $DEPS
cc -o $3 $DEPS
