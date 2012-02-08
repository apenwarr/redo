if [ -e ifcreate1.dep ]; then
	redo-ifchange ifcreate1.dep
else
	redo-ifcreate ifcreate1.dep
fi
echo $$ >>ifcreate1.log
