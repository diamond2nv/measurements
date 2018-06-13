# -*- coding: utf-8 -*-
"""
Created on Thu May  3 14:33:40 2018

@author: QPL
"""

# -*- coding: utf-8 -*-
"""
Created on Thursday April 03 14:43:00 2018

@author: Daniel White

map script designed to use a NI box for triggering scanning mirrors
"""

import datetime
import os.path
from measurements.libs import mapper 
import sys
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 1
delayBetweenRows = 1

xLims = (22, 32)  # (10, 100)
xStep = 1

yLims = (65, 75)  # (10, 140)
yStep = 1

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments
GalvoCtrl = mscan.GalvoNI(chX= '/Dev1/ao0', chY= '/Dev1/ao1')


voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::22::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=GalvoCtrl, detectors=[voltmeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)

XYscan.run_scan()
