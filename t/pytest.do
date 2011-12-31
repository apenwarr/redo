exec >&2
[ -n "$DO_BUILT" ] && exit 0  # not relevant in minimal/do
python tstate.py
