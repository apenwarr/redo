exec >&2

fs=${1%.fs}
redo-ifchange simple.fs

rm -rf "$fs"
cp -a simple/. "$fs"

for full in "$fs"/bin/*; do
	if [ -x "$full" ]; then
		ldd "$full" | while read a b c junk; do
			[ "$b" = "=>" ] && a=$c
			if [ -e "$a" ]; then
				mkdir -p "$fs/lib" "$fs/$(dirname "$a")"
				cp -f "$a" "$fs/$a"
			fi
		done
	fi
done

redo-ifchange "$fs/bin/sh"
