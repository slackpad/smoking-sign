#!/usr/bin/env python
"""
Sign daemon process that maintains the count displayed on the sign.
"""

import datetime
import logging
import optparse
import signal
import sys
import time

from sign_controller import SignController
from sign_util import create_serial_connection, seconds_into_year

RATE_LIMIT = 1.0
SECONDS_PER_YEAR = 365 * 86400


class MockConnection(object):

    """Fake connection used for standalone testing without a serial device."""

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


def run_fixed(controller, count):
    """Run in fixed mode, maintaining a constant number on the sign.

    Args:
      controller: Controller used to communicate with the sign.
      count: Count to display on the sign.
    """
    while controller.is_alive():
        controller.set_count(int(count))
        time.sleep(RATE_LIMIT)


def run_target(controller, target):
    """Run in target mode, counting up to an annual target.

    Args:
      controller: Controller used to communicate with the sign.
      target: Target to count to by the end of the year.
    """
    rate_per_second = float(target) / SECONDS_PER_YEAR
    while controller.is_alive():
        now = datetime.datetime.now()
        now_seconds = seconds_into_year(now)
        count = now_seconds * rate_per_second
        controller.set_count(int(count))
        time.sleep(RATE_LIMIT)


def go():
    """Main daemon function."""
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

    if options.mock:
        connection = MockConnection()
    else:
        connection = create_serial_connection(options.port)

    controller = SignController(connection)
    controller.start()

    def cleanup(signal, frame):
        logging.info('Interrupted, cleaning up...')
        controller.request_exit()
    signal.signal(signal.SIGINT, cleanup)

    logging.info('Waiting for cursor sync...')
    controller.ping()
    while controller.get_cursor() != 0:
        logging.debug(controller.get_cursor())
        time.sleep(1.0)

    logging.info('Running test patterns...')
    controller.set_count(888888)
    time.sleep(2.0)
    controller.set_count(0)
    time.sleep(2.0)

    if options.fixed is not None:
        count = int(options.fixed)
        logging.info('Running fixed mode for %d...', count)
        run_fixed(controller, count)
    else:
        target = int(options.target)
        logging.info('Running target mode for %d...', target)
        run_target(controller, target)

    controller.request_exit()
    controller.join()

if __name__ == '__main__':
    go()
