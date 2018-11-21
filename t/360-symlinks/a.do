printf x >>a.ran
rm -f dir/$2.1 $2.2 $2.3 $2.final
echo foo >$2.final
ln -s $2.final $2.3
ln -s $PWD/$2.3 $2.2
ln -s ../$2.2 dir/$2.1
ln -s dir/$2.1 $3
