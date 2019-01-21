# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato

map script designed to use a NI box for triggering the old acton spectro + ANC300 serial interface for the piezos
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
#     Parameters      #

delayBetweenPoints = 0.5
delayBetweenRows = 0.5

xLims = (0, 1)  # (10, 100)
xStep = 0.3


voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments
#attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL6::INSTR', chX=1, chY=2)
#spectroCtrl = mdet.ActonLockinCtrl(lockinVisaAddress=r"GPIB0::14::INSTR")
lockinCtrl = mscan.LockInDAC (visa_address = r'GPIB0::12::INSTR', channels = [1])
spectroCtrl2 = mdet.PylonNICtrl(sender_port="/Weetabix/port1/line4", receiver_port="/Weetabix/port1/line7")

#voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::22::INSTR')

#d = datetime.datetime.now()
#voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=lockinCtrl, detectors=[spectroCtrl2])
XYscan.set_range(xLims=xLims, xStep=xStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
XYscan.run_scan()

#XYscan.save_to_txt(voltsFilePath, array=XYscan.counts[1], flatten=True)

# it kind of works but there's still something strange going on