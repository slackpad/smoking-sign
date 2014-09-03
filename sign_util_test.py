import datetime
import unittest

from sign_util import *


class TestHexify(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(hexify(''), '')

    def test_with_data(self):
        data = ' 12345'
        self.assertEqual(hexify(data), '20:31:32:33:34:35')


class TestSecondsIntoYear(unittest.TestCase):

    def test_basic(self):
        now = datetime.datetime(2014, 1, 1, 0, 0, 5)
        self.assertEqual(seconds_into_year(now), 5)

        now = datetime.datetime(2014, 1, 2, 0, 0, 0)
        self.assertEqual(seconds_into_year(now), 86400)

        now = datetime.datetime(2014, 2, 1, 0, 0, 0)
        self.assertEqual(seconds_into_year(now), 31 * 86400)

if __name__ == '__main__':
    unittest.main()
