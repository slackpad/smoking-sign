#!/usr/bin/env python

import threading
import time
import unittest

from sign_controller import SignController

class MockConnection(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.read_stream = ''
        self.write_stream = ''

    def add_for_read(self, buf):
        with self.lock:
            self.read_stream += buf

    def wait_for_read(self):
        start = time.time()
        while time.time() - start < 1.0:
            with self.lock:
                if len(self.read_stream) == 0:
                    return True
        return False

    def read(self, size):
        with self.lock:
            grab = self.read_stream[:size]
            self.read_stream = self.read_stream[size:]
            return grab

    def write(self, buf):
        with self.lock:
            self.write_stream += buf

    def get_data_written(self):
        with self.lock:
            return self.write_stream

def wait_for_count(controller, count):
    start = time.time()
    while time.time() - start < 1.0:
        if controller.get_count() == count:
            return True
    return False

def wait_for_cursor(controller, cursor):
    start = time.time()
    while time.time() - start < 1.0:
        if controller.get_cursor() == cursor:
            return True
    return False

def cursor(pos):
    return chr(0x1b) + chr(0x59) + chr(0x2a) + chr(pos + 0x45)

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

        update = cursor(0) + '123456' + cursor(1)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 123456))
        self.assertTrue(wait_for_cursor(controller, 1))

        update = cursor(0) + '654321' + cursor(1)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 654321))
        self.assertTrue(wait_for_cursor(controller, 1))

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

        connection.add_for_read(chr(0x1b))
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        connection.add_for_read(chr(0x1b) + 'xxxxxxxx')
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        connection.add_for_read('123x56pffft')
        self.assertTrue(connection.wait_for_read())
        self.assertTrue(wait_for_count(controller, None))
        self.assertTrue(wait_for_cursor(controller, None))

        update = cursor(0) + '123456' + cursor(1)
        connection.add_for_read(update)
        self.assertTrue(wait_for_count(controller, 123456))
        self.assertTrue(wait_for_cursor(controller, 1))

        controller.request_exit()
        controller.join()

if __name__ == '__main__':
    unittest.main()
