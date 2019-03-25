# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato

use this for the delay line sweep
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
delayBetweenRows = 1
xLims = (0, 300)  # (10, 100)
xStep = 1


voltsDirectory = r'E:/MEASUREMENTS/Zak/DelayStage Sweep'

#######################
# instruments
#attoScannerCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL6::INSTR', chX=1, chY=2)
#attoPiezoCtrl = mscan.AttocubeVISAstepper(VISA_address=r'ASRL6::INSTR',channels=[4],nb_of_clicks_per_deg=928./5)
#attoMagnetCtrl = mscan.MagnetAttocube( tolerance=0.001, nr_tolerance_reps=5)
#spectroCtrl = mdet.ActonLockinCtrl(lockinVisaAddress=r"GPIB0::14::INSTR")
lockinCtrl = mscan.LockInDAC (visa_address = r'GPIB0::12::INSTR', channels = [1])
#spectroCtrl2 = mdet.PylonNICtrl(sender_port="/Weetabix/port1/line4", receiver_port="/Weetabix/port1/line7")
delayCtrl = mscan.NewportDelayStage(chX = u'ASRL23::INSTR')
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=u'GPIB0::23::INSTR', mode='voltage', agilent=True, work_folder=None)

#highfinese = mdet.HighFinese(channel=2)

#tempCtrl =  mdet.LakeShore(address='COM5',channel='A')


d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=delayCtrl, detectors=[voltmeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
XYscan.init_detectors(XYscan._detectors)
XYscan.set_back_to_zero()
XYscan.run_scan()

## Print output
#
xdata = XYscan.xPositions
print ('Output :',XYscan.detector_readout_0.flatten())
try:
    print ('Output :',XYscan.detector_readout_1.flatten())
except:
    print ('No device # 2 found')
try:
    print ('Output :',XYscan.detector_readout_2.flatten())
except:
    print ('No device # 3 found')
# save the voltage data
#np.savetxt(voltsFilePath, np.transpose([xdata,XYscan.detector_readout_0.flatten()]))
#
## it kind of works but there's still something strange going on