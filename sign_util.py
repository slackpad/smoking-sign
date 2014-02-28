"""
Small utility functions.
"""

import datetime

CURSOR_HOME = chr(0x45)
CURSOR_LEFT = chr(0x15)
CURSOR_MAGIC_1 = chr(0x59)
CURSOR_MAGIC_2 = chr(0x2a)
ESCAPE = chr(0x1b)

def hexify(buf):
    """Return a sequence of bytes as a hexified string.

    Args:
      buf: Bytes to convert.

    Returns:
      String with the hex value of each byte, separated with colons.
    """
    return ':'.join('{0:02x}'.format(ord(c)) for c in buf)

def seconds_into_year(now):
    """Compute the number of seconds into the current year.

    Args:
      now: Current time.

    Returns:
      Number of seconds since January 1 at midnight on the same year as now.
    """
    year_start = datetime.datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
    return (now - year_start).total_seconds()
