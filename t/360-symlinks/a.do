echo x >>a.ran
rm -f $2.extra
echo foo >$2.extra
ln -s $2.extra $3
