set +e
( . ./shelltest.od )
RV=$?
case $RV in
	0) exit 0 ;;
	42) exit 0 ;;
	*) exit 1 ;;
esac
