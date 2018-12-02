printf x >>$1.log
redo-always

read want <want

case $want in
  err) exit 10 ;;
  nil) exit 0 ;;
  add) printf x >>$3; exit 0 ;;
  *) exit 80 ;;
esac
