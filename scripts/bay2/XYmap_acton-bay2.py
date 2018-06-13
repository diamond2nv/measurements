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

xLims = (110, 124)  # (10, 100)
xStep = 0.5

yLims = (50, 64)  # (10, 140)
yStep = 0.5

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'

#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL13::INSTR', chX=1, chY=2)
spectroCtrl = mdet.ActonNICtrl(sender_port="/Weetabix/port2/line0",
                               receiver_port="/Weetabix/port2/line4")
multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::13::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=attoCtrl, detectors=[spectroCtrl, multimeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
XYscan.run_scan()

XYscan.save_to_txt(voltsFilePath, array=XYscan.counts[1], flatten=True)

