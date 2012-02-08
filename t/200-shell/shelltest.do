set +e
export SHELLTEST_QUIET=1
cd ..
( . ./shelltest.od )
RV=$?
case $RV in
	40) exit 0 ;;
	42) exit 0 ;;
	*) exit 1 ;;
esac
