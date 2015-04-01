smoking-sign
============

Small set of scripts to control an [electronic sign](http://bit.ly/1nJyENk) that
counts up the number of smoking deaths so far in the current year. The sign is
ancient and uses an ADDS Viewport terminal to control it, so this probably doesn't
have too much mass appeal.

This was designed to run on a Raspberry Pi connected to the sign (in place of
the terminal) via a GearMo USB RS-232 adapter (FTDI chipset). The Python script
sends the same commands as the old terminal to update the cursor position and
command the count displayed on the sign. There's a mode that counts up to a
target value over the course of a year, as well as a mode that displays a
fixed number up on the sign.

The sign controller is broken out as a separate class for possible integration
with other applications.
