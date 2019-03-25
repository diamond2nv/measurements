# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 12:30:11 2018

@author: QPL
"""

import datetime
import os.path
from measurements.libs.QPLMapper import mapper 
import sys
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      

delayBetweenPoints = 0.1
delayBetweenRows = 0.1
voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments

GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=-5., max_limit=5.)
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL13::INSTR')
dummyAPD = mdet.dummyAPD(voltsDirectory)

a = 3.336
b = -0.1999
d = 0.03
xStep = 0.0005


x0 = a
y0 = b
XYopt = mapper.XYOptimizer(scanner_axes= GalvoCtrl, detectors=[voltmeterCtrl])
XYopt.set_scan_range (scan_range=d, scan_step=xStep)
XYopt.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
XYopt.initialize(x0=x0, y0=y0)
a,b = XYopt.run_optimizer (close_instruments=False, silence_errors = False)