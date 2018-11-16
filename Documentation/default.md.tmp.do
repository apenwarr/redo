redo-ifchange ../version/vars $2.md
. ../version/vars
cat - $2.md <<-EOF
	% $2(1) Redo $TAG
	% Avery Pennarun <apenwarr@gmail.com>
	% $DATE
EOF
