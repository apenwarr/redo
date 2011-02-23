#!/usr/bin/env python

import os, os.path, sqlite3, sys

if "DO_BUILT" in os.environ:
    sys.exit(0)

print >>sys.stderr, "Flushing redo cache..."

db_file = os.path.join(os.environ["REDO_BASE"], ".redo", "db.sqlite3")
db_con = sqlite3.connect(db_file, timeout=5000)

db_con.executescript("pragma synchronous = off;"
                     "update Files set checked_runid=checked_runid-1, "
                     "       changed_runid=changed_runid-1, "
                     "       failed_runid=failed_runid-1;")

db_con.commit()

db_con.close()

