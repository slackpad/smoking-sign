#!/usr/bin/env python
"""
Sign daemon which updates the count over time.
"""

import datetime
import logging
import optparse
import serial
import sys
import time

from sign_controller import SignController

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', default='/dev/ttyUSB0')
parser.add_option('-t', '--target', dest='target', default=443000)
parser.add_option('-f', '--fixed', dest='fixed', default=None)
(options, args) = parser.parse_args()

connection = serial.Serial(options.port,
                           4800,
                           timeout=1,
                           bytesize=serial.SEVENBITS,
                           parity=serial.PARITY_ODD,
                           stopbits=serial.STOPBITS_TWO,
                           xonxoff=False,
                           rtscts=False,
                           dsrdtr=False)
controller = SignController(connection)

logging.info('Waiting for cursor sync...')
while controller.get_cursor() != 0:
    pass

logging.info('Running test patterns...')
controller.set_count(888888)
time.sleep(5.0)
controller.set_count(0)
time.sleep(5.0)

if options.fixed is not None:
    target = int(options.fixed)
    while True:
        controller.set_count(target)
        time.sleep(60.0 / 10)

# TODO - Implement the target option
