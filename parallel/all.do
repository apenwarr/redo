start=$(date +%s)
redo-ifchange a b c
end=$(date +%s)
if [ "$(( $end - $start ))" -lt "3" ]; then
  echo "PASS: parallel build" >&2
else
  echo "FAIL: parallel build" >&2
fi
