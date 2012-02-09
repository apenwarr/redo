rm -f log
echo ok >>log
this-should-cause-a-fatal-error
echo fail >>log  # this line should never run
