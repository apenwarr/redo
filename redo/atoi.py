
def atoi(v):
    try:
        return int(v or 0)
    except ValueError:
        return 0
