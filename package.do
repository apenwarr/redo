exec >&2

if ! which fpm >/dev/null 2>&1; then
  echo "To build system packages, you need fpm"
  echo "You can get it using the ruby gem 'fpm':"
  echo "    gem install fpm    (as root)"
  exit 1
fi

if which rpmbuild >/dev/null 2>&1; then
  redo rpm
elif which dpkg >/dev/null 2>&1; then
  redo deb
else
  echo "Your packaging system is not supported"
  exit 1
fi
