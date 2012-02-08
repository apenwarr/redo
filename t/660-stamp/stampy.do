echo $$ >>stampy.log
redo-ifchange inp bob
cat inp
cd ..
redo-stamp <660-stamp/inp
