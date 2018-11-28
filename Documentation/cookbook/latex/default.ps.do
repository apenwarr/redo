exec >&2
redo-ifchange "$2.dvi"
dvips -o "$3" "$2.dvi"
