#!/usr/bin/env python
"""Generate a docker 1.0-style manifest for a docker image."""
import json, os, sys, time

j = json.load(open('template.json'))
layerid = open(sys.argv[1] + '.list.sha256').read().strip()
j['id'] = layerid

if len(sys.argv) > 2 and sys.argv[2]:
    parentid = open(sys.argv[2] + '.list.sha256').read().strip()
    j['parent'] = parentid

t = time.time()
gt = time.gmtime(t)
nsec = int(t * 1e9) % 1000000000
j['created'] = time.strftime('%Y-%m-%dT%H:%M:%S', gt) + ('.%09dZ' % nsec)

nbytes = os.stat(sys.argv[1] + '.layer').st_size
j['Size'] = nbytes

json.dump(j, sys.stdout, indent=2)
