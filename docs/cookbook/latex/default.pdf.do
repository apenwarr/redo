exec >&2
redo-ifchange "$2.dvi"
dvipdf "$2.dvi" "$3"
