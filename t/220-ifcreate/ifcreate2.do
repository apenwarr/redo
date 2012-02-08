cd ..
if [ -e 220-ifcreate/ifcreate2.dep ]; then
	redo-ifchange 220-ifcreate/ifcreate2.dep
else
	redo-ifcreate 220-ifcreate/ifcreate2.dep
fi
echo $$ >>220-ifcreate/ifcreate2.log
