import logging
import threading
import time

CURSOR_HOME = chr(0x45)
CURSOR_LEFT = chr(0x15)
CURSOR_MAGIC_1 = chr(0x59)
CURSOR_MAGIC_2 = chr(0x2a)
ESCAPE = chr(0x1b)
RATE_LIMIT = 1.0
READ_SIZE = 1024

def hexify(buf):
    """Return a sequence of bytes as a hexified string."""
    return ':'.join('{0:02x}'.format(ord(c)) for c in buf)

class SignController(threading.Thread):
    """Controller for an ancient electronic sign.

    This maintains an estimate of the state of the sign itself, and provides
    methods to update the sign's displayed numbers.
    """

    def __init__(self, connection):
        """Initialize the controller.

        The count and cursor position will remain at None until we get the
        next periodic update from the sign.

        Args:
          connection: Connection object used to communicate with the sign;
            must support read() and write() methods.
        """
        super(SignController, self).__init__()
        self.lock = threading.Lock()
        self.should_exit = False
        self.connection = connection
        self.count = None
        self.cursor = None

    def set_count(self, count):
        with self.lock:
            if self.cursor != 0:
                logging.warning('Cannot set count, cursor is %d', self.cursor)
                return

            if count <= 0:
                count = '000000'
            elif count > 999999:
                count = '999999'
            else:
                count = str(count)
                count = ' ' * (6 - len(count)) + count

            self._send(count)

    def get_count(self):
        """Get the current count displayed on the sign."""
        with self.lock:
            return self.count

    def get_cursor(self):
        """Get the current position of the cursor on the sign."""
        with self.lock:
            return self.cursor

    def request_exit(self):
        """Ask the thread to shut down."""
        self.should_exit = True

    def run(self):
        """Service I/O with the sign."""
        while not self.should_exit:
            # Lock for the duration of this read so that external queries will
            # get the latest information based on the whole update (there can
            # be multiple cursor commands in one response and we never want
            # the intermediate ones).
            with self.lock:
                buf = self.connection.read(READ_SIZE)
                if len(buf) > 0:
                    self._parse(buf)
                    self._manage_cursor()

    def _parse(self, buf):
        """Parse a response from the sign."""
        while len(buf) > 0:
            byte_count = len(buf)
            if byte_count >= 4 and buf[0] == ESCAPE:
                buf = self._parse_escape(buf)
            elif byte_count >= 6:
                buf = self._parse_count(buf)
            else:
                logging.warning('Unexpected data: %s', hexify(buf))
                break

    def _manage_cursor(self):
        """Manage the cursor position so we are ready to update the count at any
        time.

        Our goal is always to move the cursor to the home position. This gets
        called after we get an update from the sign, which should always be a
        quiet time (it will be about a minute before the sign sends another
        periodic update). Since this is based on feedback we always add a delay
        after we make an adjustment so we never blast the sign with updates.
        """
        if self.cursor is not None and self.cursor != 0:
            logging.info('Adjusting cursor from %d', self.cursor)
            self._send(CURSOR_LEFT)
            time.sleep(RATE_LIMIT)

    def _parse_escape(self, buf):
        """Parse an escape sequence.

        These contain the escape sequence 1b:59:2a followed by the cursor
        position byte. The value 0x45 represents the home position at the
        far left side of the count displayed on the sign.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        if buf[0] == ESCAPE \
           and buf[1] == CURSOR_MAGIC_1 \
           and buf[2] == CURSOR_MAGIC_2:
            self.cursor = ord(buf[3]) - ord(CURSOR_HOME)
        else:
            logging.warning('Unknown escape sequence: %s', hexify(buf))
        return buf[4:]

    def _parse_count(self, buf):
        """Parse a count update for with the digits on the sign.

        These contain the six digits that were entered, with possible spaces for
        leading digits.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        try:
            self.count = int(buf[0:6])
        except ValueError:
            logging.warning('Unexpected count value: %s', hexify(buf))
        return buf[6:]

    def _send(self, buf):
        """Send some data to the sign."""
        self.connection.write(buf)
        self.connection.flush()
