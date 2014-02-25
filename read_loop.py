#!/usr/bin/env python
"""
Simple utility used to sniff serial data going to or coming from the sign.
"""

import optparse
import serial
import sys

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', default='/dev/ttyUSB0')
(options, args) = parser.parse_args()

ser = serial.Serial(options.port,
                    4800,
                    timeout=1,
                    bytesize=serial.SEVENBITS,
                    parity=serial.PARITY_ODD,
                    stopbits=serial.STOPBITS_TWO,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False)

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
