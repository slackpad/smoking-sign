"""
Unit tests for the sign controller.
"""

import logging
import threading
import time
import unittest

from sign_controller import SignController
from sign_util import *

logging.basicConfig(level=logging.DEBUG)

class MockConnection(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.read_stream = ''
        self.write_stream = ''

    def add_for_read(self, buf):
        with self.lock:
            self.read_stream += buf

    def wait_for_read(self, timeout=1.0):
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if len(self.read_stream) == 0:
                    return True
        return False

    def wait_for_write(self, timeout=1.0):
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if len(self.write_stream) > 0:
                    written = self.write_stream
                    self.write_stream = ''
                    return written
        return ''

    def read(self, size):
        with self.lock:
            grab = self.read_stream[:size]
            self.read_stream = self.read_stream[size:]
            return grab

    def write(self, buf):
        with self.lock:
            self.write_stream += buf

    def flush(self):
        pass

def wait_for_count(controller, count, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        if controller.get_count() == count:
            return True
    return False

def wait_for_cursor(controller, cursor, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        if controller.get_cursor() == cursor:
            return True
    return False

def set_cursor(pos):
    return ESCAPE + CURSOR_MAGIC_1 + CURSOR_MAGIC_2 + \
        chr(ord(CURSOR_HOME) + pos)

class TestSignController(unittest.TestCase):

    def test_init(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        controller.request_exit()
        controller.join()

    def test_periodic_updates(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        update = set_cursor(0) + '123456' + set_cursor(0)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 123456))
        self.assertTrue(wait_for_cursor(controller, 0))

        update = set_cursor(0) + '654321' + set_cursor(0)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 654321))
        self.assertTrue(wait_for_cursor(controller, 0))

        controller.request_exit()
        controller.join()

    def test_cursor_adjust(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        connection.add_for_read(set_cursor(0))
        self.assertTrue(wait_for_cursor(controller, 0))

        connection.add_for_read(set_cursor(1))
        self.assertTrue(wait_for_cursor(controller, 1))
        self.assertEqual(connection.wait_for_write(), CURSOR_LEFT)

        for i in range(5, 0, -1):
            connection.add_for_read(set_cursor(i))
            self.assertTrue(wait_for_cursor(controller, i))
            self.assertEqual(connection.wait_for_write(), CURSOR_LEFT)

        connection.add_for_read(set_cursor(0))
        self.assertTrue(wait_for_cursor(controller, 0))

        controller.request_exit()
        controller.join()

    def test_ping(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        self.assertTrue(wait_for_cursor(controller, None))

        controller.ping()
        self.assertEqual(connection.wait_for_write(), CURSOR_LEFT)

        connection.add_for_read(set_cursor(0))
        self.assertTrue(wait_for_cursor(controller, 0))

        controller.request_exit()
        controller.join()

    def test_set_count(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        connection.add_for_read(set_cursor(1))
        self.assertTrue(wait_for_cursor(controller, 1))
        self.assertEqual(connection.wait_for_write(), CURSOR_LEFT)
        controller.set_count(123456)
        self.assertEqual(connection.wait_for_write(), '')
        self.assertEqual(controller.get_count(), None)

        connection.add_for_read(set_cursor(0))
        self.assertTrue(wait_for_cursor(controller, 0))

        controller.set_count(123456)
        self.assertEqual(connection.wait_for_write(), '123456')
        connection.add_for_read('123456' + set_cursor(0))
        self.assertTrue(wait_for_count(controller, 123456))

        controller.set_count(99)
        self.assertEqual(connection.wait_for_write(), '    99')
        connection.add_for_read('    99' + set_cursor(0))
        self.assertTrue(wait_for_count(controller, 99))

        controller.set_count(0)
        self.assertEqual(connection.wait_for_write(), '000000')
        connection.add_for_read('000000' + set_cursor(0))
        self.assertTrue(wait_for_count(controller, 0))

        controller.set_count(-1)
        self.assertEqual(connection.wait_for_write(), '000000')
        connection.add_for_read('000000' + set_cursor(0))
        self.assertTrue(wait_for_count(controller, 0))

        controller.set_count(1000000)
        self.assertEqual(connection.wait_for_write(), '999999')
        connection.add_for_read('999999' + set_cursor(0))
        self.assertTrue(wait_for_count(controller, 999999))

        controller.request_exit()
        controller.join()

    def test_bad_messages(self):
        connection = MockConnection()
        controller = SignController(connection)
        controller.start()

        connection.add_for_read('xx')
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        connection.add_for_read(ESCAPE)
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        connection.add_for_read(ESCAPE + 'xxxxxxxx')
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        connection.add_for_read('123x56pffft')
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        update = set_cursor(0) + '123456' + set_cursor(0)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 123456))
        self.assertTrue(wait_for_cursor(controller, 0))

        controller.request_exit()
        controller.join()

if __name__ == '__main__':
    unittest.main()
