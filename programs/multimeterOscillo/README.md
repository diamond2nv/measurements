Raphael Proux 15/03/2017

Use keithleyOscilloQT.py for nice graphical user interface
The keithleyOscillo.py program is an older version much slower, 
but kept as a possible alternative if the other fails.

Use the config file for setting the VISA address of the device. 
You can find it using NI Max.
Note it should handle GPIB or Serial interface without issues.


IMPORTANT :

This program is tested with Keithley 2000 multimeters. 
Other benchtop multimeters (Agilent,...) should work similarly 
but an adaptation work may be needed.