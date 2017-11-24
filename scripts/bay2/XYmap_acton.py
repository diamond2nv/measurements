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
if sys.version_info.major == 3:
    from importlib import reload

reload (mapper)

#######################
#     Parameters      #

delayBetweenPoints =0.5
delayBetweenRows = 0.5

xLims = (10, 100)  # (10, 80)
xStep = 1

yLims = (10, 140)  # (10, 140)
yStep = 1

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'

#######################
# instruments
attoCtrl = mapper.AttocubeVISA(VISA_address=r'ASRL11::INSTR', axisX=2, axisY=1)
spectroCtrl = mapper.ActonNICtrl(sender_port="/SmallNIbox/port1/line3",
                         receiver_port = "/SmallNIbox/port1/line2")
voltmeterCtrl = mapper.VoltmeterCtrl(VISA_address=r'GPIB0::13::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner=attoCtrl, detector=spectroCtrl, voltmeter=voltmeterCtrl)
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
XYscan.run_scan()

XYscan.save_volts(voltsFilePath, flatten=True)

