redo-ifchange template.json "$1.layers"
layers=$(cat "$1.layers")

dir=$3.tmp
rm -rf "$dir"
mkdir -p "$dir"

# Build all layers in parallel
for layer in $layers; do
	echo "$layer.list.sha256"
	echo "$layer.layer"
done | xargs redo-ifchange

ids=
parent=
for layer in $layers; do
	read cid <$layer.list.sha256
	echo "layer: $cid $layer" >&2
	
	# docker seems to order its image tarballs latest-first,
	# so the base layer is last.  We'll create in order from
	# base layer to final layer, but create a tarball in the
	# opposite order.
	ids="$cid $ids"  # prepend

	mkdir "$dir/$cid"
	echo "1.0" >$dir/$cid/VERSION
	./dockjson.py "$layer" "$parent" >$dir/$cid/json
	ln "$layer.layer" "$dir/$cid/layer.tar"
	parent=$layer
done <$1.layers

tar -C "$dir" -cf - $ids >$3
rm -rf "$dir"
