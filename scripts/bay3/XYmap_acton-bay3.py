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

xLims = (62, 67)  # (10, 100)
xStep = 1

yLims = (83, 87)  # (10, 140)
yStep = 1

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL6::INSTR', chX=2, chY=1)
spectroCtrl = mdet.ActonLockinCtrl(lockinVisaAddress=r"GPIB0::14::INSTR")
spectroCtrl2 = mdet.PylonNICtrl(sender_port="/Weetabix/port1/line3", receiver_port="/Weetabix/port1/line2")

voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::22::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=attoCtrl, detectors=[spectroCtrl2])    #, voltmeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
XYscan.run_scan()

#XYscan.save_to_txt(voltsFilePath, array=XYscan.counts[1], flatten=True)

