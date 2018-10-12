echo $$ >>stampy.log
redo-ifchange inp bob
cat inp
cd ..
redo-stamp <s60-stamp/inp
