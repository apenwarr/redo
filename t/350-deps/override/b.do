redo-ifchange a
printf '%s-%s-b\n' "$(cat a)" "$(cat stamp)" >$3
