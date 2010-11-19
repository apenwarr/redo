redo-ifchange 1.n0 2.n0 3.n0
DEPS=$(seq 10 | sed 's/$/.n1/')
redo-ifchange $DEPS
