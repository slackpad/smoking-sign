#!/usr/bin/env python
"""
Simple utility used to sniff serial data going to or coming from the sign.
"""

import optparse
import sys

from sign_util import create_serial_connection

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', default='/dev/ttyUSB0')
(options, args) = parser.parse_args()

ser = create_serial_connection(options.port)
while True:
    data = ser.read(1024)
    hexified = ':'.join('{0:02x}'.format(ord(c)) for c in data)
    asciified = ''
    for c in data:
        if ord(c) >= 32 and ord(c) <= 126:
            asciified += c
        else:
            asciified += '#'
    if len(data) > 0:
        print "%s %s %s" % (len(data), hexified, asciified)
        sys.stdout.flush()
