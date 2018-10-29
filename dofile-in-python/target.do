#!/usr/bin/env python3.5
from subprocess import run
from datetime import datetime

run(['redo-ifchange', 'source'], close_fds=False)
print(datetime.now().timestamp())
