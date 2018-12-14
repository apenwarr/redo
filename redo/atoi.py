"""Simple integer conversion helper."""

def atoi(v):
    """Convert v to an integer, or return 0 on error, like C's atoi()."""
    try:
        return int(v or 0)
    except ValueError:
        return 0
