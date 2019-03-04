# redo - a recursive build system

Smaller, easier, more powerful, and more reliable than `make`.

This is an implementation of [Daniel J. Bernstein's redo
build system](http://cr.yp.to/redo.html).  He never released his
version, so other people have implemented different variants based on his
published specification.

This version, sometimes called apenwarr/redo, is probably the most advanced
one, including parallel builds, improved logging, extensive automated tests,
and helpful debugging features.

To build and test redo, run:
```sh
	./do -j10 test
```

To install it, run something like this:
```sh
	DESTDIR= PREFIX=/usr/local ./do -j10 install
```

---

- View the [documentation](https://redo.rtfd.io) via readthedocs.org
- Visit the [source code](https://github.com/apenwarr/redo) on github
- Discussions and support via the
    mailing list ([archives](https://groups.google.com/group/redo-list)). 
    You can subscribe by sending any email message to
    `redo-list+subscribe@googlegroups.com` (note the plus sign).  You can
    send questions or feedback (with or without subscribing) by sending
    messages to `redo-list@googlegroups.com`.
