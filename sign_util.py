"""
Small utility functions.
"""

import datetime
import serial

CURSOR_HOME = chr(0x45)
CURSOR_LEFT = chr(0x15)
CURSOR_MAGIC_1 = chr(0x59)
CURSOR_MAGIC_2 = chr(0x2a)
ESCAPE = chr(0x1b)


def create_serial_connection(port):
    """Return a serial connection with the correct settings for the real sign.

    Args:
      port: Device name to connect to (eg. '/dev/ttyUSB0').

    Returns:
      Connection object.
    """
    return serial.Serial(port,
                         4800,
                         timeout=1,
                         bytesize=serial.SEVENBITS,
                         parity=serial.PARITY_ODD,
                         stopbits=serial.STOPBITS_TWO,
                         xonxoff=False,
                         rtscts=False,
                         dsrdtr=False)


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
