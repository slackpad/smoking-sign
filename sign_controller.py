import logging
import threading

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

    def run(self):
        """Service I/O with the sign."""
        while not self.should_exit:
            buf = self.connection.read(1024)
            while len(buf) > 0:
                byte_count = len(buf)
                if byte_count >= 4 and ord(buf[0]) == 0x1b:
                    buf = self._parse_escape(buf)
                elif byte_count >= 6:
                    buf = self._parse_count(buf)
                else:
                    logging.warning('Unexpected data: %s', hexify(buf))
                    break

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

    def _parse_escape(self, buf):
        """Parse an escape sequence.

        These contain the escape sequence 1b:59:2a followed by the cursor
        position byte. The value 0x45 represents the "home" position at the
        far left side of the count displayed on the sign.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        if ord(buf[0]) == 0x1b \
           and ord(buf[1]) == 0x59 \
           and ord(buf[2]) == 0x2a:
            with self.lock:
                self.cursor = ord(buf[3]) - 0x45
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
            with self.lock:
                self.count = int(buf[0:6])
        except ValueError:
            logging.warning('Unexpected count value: %s', hexify(buf))
        return buf[6:]

    def _send(self, buf):
        """Send some data to the sign."""
        self.connection.write(buf)
