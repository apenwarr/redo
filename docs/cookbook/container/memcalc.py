#!/usr/bin/env python
import os, sys
st = os.stat(sys.argv[1])
megabytes = st.st_size // 1024 // 1024
# initrd size is limited to 50% of available RAM.  To be safe, we'll
# request at least 3x initrd size, and no less than 64M.
need = megabytes * 3 + 64
print("%dM" % need)
