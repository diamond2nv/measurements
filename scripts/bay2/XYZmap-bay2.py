# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, mauro brotons

XYZ map script
"""

import datetime
import os.path
from measurements.libs.QPLMapper import mapper 
import sys
import numpy as np
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 0.5
delayBetweenRows = 0.5

xLims = (1, 4)  # (10, 100)
xStep = 2

yLims = (1, 4)  # (10, 140)
yStep = 2

zLims = (-2, 2)  # (10, 140)
zStep = 2

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'

#######################
# instruments
testscanCtrl = mscan.TestScanner(address=1, channels=[1,2,3])
spectroCtrl = mdet.ActonNICtrl(sender_port="/Weetabix/port2/line0",
                               receiver_port="/Weetabix/port2/line4")
multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL17::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program

XYZ_scan = mapper.XYScan(scanner_axes=[testscanCtrl[0], testscanCtrl[1]], detectors=[spectroCtrl, multimeterCtrl])
XYZ_scan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYZ_scan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)

total_counts = []

zNbOfSteps = int(abs(np.floor((float(zLims[1]) - float(zLims[0])) / float(zStep))) + 1)
zPositions = np.linspace(zLims[0], zLims[1], zNbOfSteps)


for z in zPositions:
    testscanCtrl[2].move(z)
    
    XYZ_scan.run_scan(close_instruments=False)
    total_counts.append(XYZ_scan.counts)
    
XYZ_scan.close_instruments()   

XYZ_scan.save_to_txt(voltsFilePath, array=XYZ_scan.counts[1], flatten=True)

