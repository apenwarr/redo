DEPS=$(./seq 10 | sed 's/$/.n1/')
redo-ifchange $DEPS
