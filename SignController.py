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
        self.connection = connection
        self.lock = threading.Lock()
        self.count = None
        self.cursor = None

    def run(self):
        """Service I/O with the sign."""
        while True:
            buf = self.connection.read(1024)
            if len(buf) > 0:
                self._receive(buf)

    def _receive(self, buf):
        """Handle some data from the sign."""
        with self.lock:
            byte_count = len(buf)
            if byte_count == 4:
                self._parse_cursor(buf)
            elif byte_count == 10:
                self._parse_count_update(buf)
            elif byte_count == 14:
                self._parse_periodic_update(buf)
            else:
                logging.warning('Unexpected bytes: %s', hexify(buf))

    def _parse_cursor(self, buf):
        """Parse a cursor positioning message.

        These contain the escape sequence 1b:59:2a followed by the cursor
        position byte. The value 0x45 represents the "home" position at the
        far left side of the count displayed on the sign.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        if ord(buf[0]) == 0x1b \
           and ord(buf[1]) == 0x59 \
           and ord(buf[2]) == 0x2a:
            self.cursor = ord(buf[3]) - 0x45
        else:
            logging.warning('Unexpected bytes: %s', hexify(buf))
        return buf[4:]

    def _parse_count_update(self, buf):
        """Parse an update after sending a new count.

        These contain the six digits that were entered, followed by a cursor
        positioning message.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        self.count = buf[0:6]
        buf = buf[6:]
        return self._parse_cursor(buf)

    def _parse_periodic_update(self, buf):
        """Parse a periodic update from the sign.

        Thes contain a cursor positioning message, the six digits currently on
        the sign, and another cursor positioning message.

        Returns:
          Remaining (unparsed) portion of buf.
        """
        buf = self._parse_cursor(buf)
        return self._parse_count_update(buf)

    def _send(self, buf):
        """Send some data to the sign."""
        with self.lock:
            self.connection.write(buf)
