cd ..
if [ -e t/ifcreate2.dep ]; then
	redo-ifchange t/ifcreate2.dep
else
	redo-ifcreate t/ifcreate2.dep
fi
echo $$ >>t/ifcreate2.log
