# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 14:40:05 2017

@author: QPL
"""

import LockIn7265 as li
import time
import pylab as py

loc = li.LockIn7265(r'GPIB0::12::INSTR')
no_reads = 10800
i = 0
mag_b = []
pha_b = []
filename = "C:\Users\QPL\Desktop\Temp-meas\warmup-current-phase"
while i < no_reads:
    mag = float(loc.dev.query("MAG."))*1e9
    mag_b.append(mag)
    pha = float(loc.dev.query("PHA."))
    pha_b.append(pha)
    print (mag, pha)
    i += 1
    time.sleep(1)

py.savetxt(filename + time.strftime('%Y-%m-%d-%H-%M.txt') , py.array([mag_b, pha_b]).transpose(), fmt='%4.5f', delimiter=',')