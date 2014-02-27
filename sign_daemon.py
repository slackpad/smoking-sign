#!/usr/bin/env python
"""
Sign daemon which updates the count over time.
"""

import datetime
import logging
import optparse
import serial
import signal
import sys
import time

from sign_controller import SignController, hexify

class MockConnection(object):

    def __init__(self):
        self.first = True

    def read(self, size):
        if self.first:
            self.first = False
            return chr(0x1b) + chr(0x59) + chr(0x2a) + chr(0x45)
        else:
            time.sleep(1.0)
            return ''

    def write(self, buf):
        pass

    def flush(self):
        pass

def make_connection(mock, port):
    if mock:
        return MockConnection()
    else:
        return serial.Serial(port,
                             4800,
                             timeout=1,
                             bytesize=serial.SEVENBITS,
                             parity=serial.PARITY_ODD,
                             stopbits=serial.STOPBITS_TWO,
                             xonxoff=False,
                             rtscts=False,
                             dsrdtr=False)

def run_fixed(controller, target):
    while controller.is_alive():
        controller.set_count(int(target))
        time.sleep(60.0 / 10)

def run_target(controller, target):
    pass

def go():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG)

    parser = optparse.OptionParser()
    parser.add_option('-f', '--fixed', dest='fixed', default=None,
                      help='Set a fixed count on the sign')
    parser.add_option('-p', '--port', dest='port', default='/dev/ttyUSB0',
                      help='Serial port device')
    parser.add_option('-m', '--mock', dest='mock', action='store_true',
                      help='Use a mock sign connection for local testing')
    parser.add_option('-t', '--target', dest='target', default=443000,
                      help='Annual target to automatically count up to')
    (options, args) = parser.parse_args()

    connection = make_connection(options.mock, options.port)
    controller = SignController(connection)
    controller.start()

    def cleanup(signal, frame):
        logging.info('Interrupted, cleaning up...')
        controller.request_exit()
    signal.signal(signal.SIGINT, cleanup)

    logging.info('Waiting for cursor sync...')
    while controller.get_cursor() != 0:
        logging.debug(controller.get_cursor())
        time.sleep(1.0)

    logging.info('Running test patterns...')
    controller.set_count(888888)
    time.sleep(5.0)
    controller.set_count(0)
    time.sleep(5.0)

    if options.fixed is not None:
        target = int(options.fixed)
        logging.info('Running fixed mode for %d...', target)
        run_fixed(controller, target)
    else:
        target = int(options.target)
        logging.info('Running target mode for %d...', target)
        run_target(controller, target)

    controller.join()

if __name__ == '__main__':
    go()
