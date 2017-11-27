# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato

map script designed to use a NI box for triggering the old acton spectro + ANC300 serial interface for the piezos
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

delayBetweenPoints = 0.5
delayBetweenRows = 0.5

xLims = (10, 100)  # (10, 100)
xStep = 1

yLims = (10, 140)  # (10, 140)
yStep = 1

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'

#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL11::INSTR', axisX=2, axisY=1)
spectroCtrl = mdet.ActonNICtrl(sender_port="/SmallNIbox/port1/line3",
                               receiver_port="/SmallNIbox/port1/line2")
voltmeterCtrl = mdet.VoltmeterCtrl(VISA_address=r'GPIB0::13::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner=attoCtrl, detectors=[spectroCtrl, voltmeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
XYscan.run_scan()

XYscan.save_volts(XYscan.counts[1], voltsFilePath, flatten=True)

