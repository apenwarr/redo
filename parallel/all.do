start=$(date +%s)
redo-ifchange a b c d e f g h i j
end=$(date +%s)
if [ "$(( $end - $start ))" -lt "10" ]; then
  echo "PASS: parallel build" >&2
else
  echo "FAIL: parallel build" >&2
fi
