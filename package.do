exec >&2

if ! which fpm >/dev/null 2>&1; then
  echo "To build system packages, you need fpm"
  echo "You can get it using the ruby gem 'fpm':"
  echo "    gem install fpm    (as root)"
  exit 1
fi

if which rpmbuild >/dev/null 2>&1; then
  type=rpm
  arch=noarch
elif which dpkg >/dev/null 2>&1; then
  type=deb
  arch=all
else
  echo "Your packaging system is not supported"
  exit 1
fi

desc=$(git describe)

DESTDIR="$(pwd)/root" redo install

fpm \
  --name redo \
  --version ${desc#redo-} \
  -C root \
  -d python \
  -a $arch \
  -s dir -t $type .

rm -rf root

