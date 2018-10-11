exec >&2

if ! which fpm >/dev/null 2>&1; then
  echo "To build system packages, you need fpm"
  echo "You can get it using the ruby gem 'fpm':"
  echo "    gem install fpm    (as root)"
  exit 1
fi

DESTDIR="$(pwd)/root" redo install

desc=$(git describe)

fpm \
  --name redo \
  --version ${desc#redo-} \
  -C root \
  -d python \
  -a all \
  -s dir -t deb .

rm -rf root
