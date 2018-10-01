#!/bin/sh
TARGETS="directory/target directory/target.xyz"

for TARGET in ${TARGETS}; do
 mv "${TARGET}" "${TARGET}.old"
 redo-ifchange "${TARGET}"
 REAL_BASENAME=$(basename "${TARGET}" .xyz)
 read -r REDO_ABSPATH REDO_BASENAME REDO_TMPFILE <"${TARGET}"
 case "${REDO_BASENAME}" in
  "${REAL_BASENAME}") echo "PASS: \${2} = ${REAL_BASENAME}" >&2 ;;
  *) echo "FAIL: \${2} = ${REDO_BASENAME} != ${REAL_BASENAME}" >&2 ;;
 esac
done
