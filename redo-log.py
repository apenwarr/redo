#!/usr/bin/env python
import errno, os, re, sys, time
import options

optspec = """
redo-log [options...] [targets...]
--
r,recursive     show build logs for dependencies too
u,unchanged     show lines for dependencies not needing to be rebuilt
f,follow        keep watching for more lines to be appended (like tail -f)
no-details      only show 'redo' recursion trace, not build output
no-colorize     don't colorize 'redo' log messages
no-status       don't display build summary line in --follow
ack-fd=         (internal use only) print REDO-OK to this fd upon starting
"""
o = options.Options(optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])
targets = extra

import vars_init
vars_init.init(list(targets))

import vars, state

already = set()
queue = []
depth = []
total_lines = 0
status = None


# regexp for matching "redo" lines in the log, which we use for recursion.
# format:
#            redo  path/to/target which might have spaces
#            redo  [unchanged] path/to/target which might have spaces
#            redo  path/to/target which might have spaces (comment)
# FIXME: use a more structured format when writing the logs.
# That will prevent false positives and negatives.  Then transform the
# structured format into a user-friendly format when printing in redo-log.
REDO_LINE_RE = re.compile(r'^redo\s+(\[\w+\] )?([^(:]+)( \([^)]+\))?\n$')


def is_locked(fid):
    return (fid is not None) and not state.Lock(fid=fid).trylock()


def catlog(t):
    global total_lines, status
    if t in already:
        return
    depth.append(t)
    already.add(t)
    if t == '-':
        f = sys.stdin
        fid = None
        logname = None
    else:
        try:
            sf = state.File(name=t, allow_add=False)
        except KeyError:
            sys.stderr.write('redo-log: %r: not known to redo.\n' % (t,))
            sys.exit(24)
        fid = sf.id
        del sf
        state.rollback()
        logname = state.logname(fid)
        f = None
    delay = 0.01
    was_locked = is_locked(fid)
    line_head = ''
    while 1:
        if not f:
            try:
                f = open(logname)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    # ignore files without logs
                    pass
                else:
                    raise
        if f:
            # Note: normally includes trailing \n.
            # In 'follow' mode, might get a line with no trailing \n
            # (eg. when ./configure is halfway through a test), which we
            # deal with below.
            line = f.readline()
        else:
            line = None
        if not line and (not opt.follow or not was_locked):
            # file not locked, and no new lines: done
            break
        if not line:
            was_locked = is_locked(fid)
            if opt.follow:
                if opt.status:
                    # FIXME use actual terminal width here
                    head = '[redo] %s ' % ('{:,}'.format(total_lines))
                    tail = ''
                    for i in reversed(depth):
                        n = os.path.basename(i)
                        if 65 - len(head) - len(tail) < len(n) + 1:
                            tail = '... ' + tail
                            break
                        else:
                            tail = n + ' ' + tail
                    status = head + tail
                    sys.stdout.flush()
                    sys.stderr.write('\r%-70.70s\r' % status)
                time.sleep(min(delay, 1.0))
                delay += 0.01
            continue
        total_lines += 1
        delay = 0.01
        if not line.endswith('\n'):
            line_head += line
            continue
        if line_head:
            line = line_head + line
            line_head = ''
        if status:
            sys.stdout.flush()
            sys.stderr.write('\r%-70.70s\r' % '')
            status = None
        g = re.match(REDO_LINE_RE, line)
        if g:
            attr, name, comment = g.groups()
            if attr == '[unchanged] ':
                if opt.unchanged:
                    if name not in already:
                        sys.stdout.write(line)
                    if opt.recursive:
                        catlog(name)
            else:
                sys.stdout.write(line)
                if opt.recursive and (not comment or comment == ' (WAITING)'):
                    assert name
                    catlog(name)
        else:
            if opt.details:
                sys.stdout.write(line)
    if status:
        sys.stdout.flush()
        sys.stderr.write('\r%-70.70s\r' % '')
        status = None
    if line_head:
        # partial line never got terminated
        print line_head
    assert(depth[-1] == t)
    depth.pop(-1)

try:
    if not targets:
        sys.stderr.write('redo-log: give at least one target; maybe "all"?\n')
        sys.exit(1)
    if opt.status < 2 and not os.isatty(2):
        opt.status = False
    if opt.ack_fd:
        ack_fd = int(opt.ack_fd)
        assert(ack_fd > 2)
        if os.write(ack_fd, 'REDO-OK\n') != 8:
            raise Exception('write to ack_fd returned wrong length')
        os.close(ack_fd)
    queue += targets
    while queue:
        t = queue.pop(0)
        if t != '-':
            print 'redo  %s' % t
        catlog(t)
except KeyboardInterrupt:
    sys.exit(200)
except IOError, e:
    if e.errno == errno.EPIPE:
        pass
    else:
        raise
