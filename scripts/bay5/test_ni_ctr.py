# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 14:10:30 2017

@author: ted
"""

from measurements.instruments import NIBox
import time

# APD counter settings
ctr_time_ms = 1000
ctr_port = 'port1/line5'

ctr = NIBox.NIBoxCounter(dt=ctr_time_ms)
ctr.set_port (ctr_port)

print ("start")
ctr.start()
print ("wait")
time.sleep (1)
print ("stop")
ctr.stop()
ctr.clear()
