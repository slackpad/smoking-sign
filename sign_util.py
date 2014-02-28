import datetime

CURSOR_HOME = chr(0x45)
CURSOR_LEFT = chr(0x15)
CURSOR_MAGIC_1 = chr(0x59)
CURSOR_MAGIC_2 = chr(0x2a)
ESCAPE = chr(0x1b)

def hexify(buf):
    """Return a sequence of bytes as a hexified string."""
    return ':'.join('{0:02x}'.format(ord(c)) for c in buf)

def seconds_into_year(now):
    year_start = datetime.datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
    return (now - year_start).total_seconds()
