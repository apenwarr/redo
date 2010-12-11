echo $$ >>stampy.log
redo-ifchange inp bob
cat inp
redo-stamp <inp
