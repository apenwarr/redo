#!/bin/sh
TARGETS="directory/target directory/target.xyz"

for TARGET in ${TARGETS}; do
 mv "${TARGET}" "${TARGET}.old"
 redo-ifchange "${TARGET}"
 read -r FILENAME BASENAME TEMPFILE <"${TARGET}"
 case "${BASENAME}" in
  target) echo "PASS: \${BASENAME} = target" >&2 ;;
  *) echo "FAIL: \${BASENAME} != target" >&2 ;;
 esac
done
