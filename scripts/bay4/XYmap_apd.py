# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato
"""

import pylab as py
import time
import datetime
import os.path
import sys
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 1
delayBetweenRows = 0.5

xLims = (0, 2)
xStep = 1

yLims = (0, 2)
yStep = 1

#voltsDirectory = r'C:\Users\ted\Desktop\temporary_meas'
#realPosDirectory = r'C:\Users\ted\Desktop\temporary_meas'

#######################
# convert to Attocube DC drive voltage
toDC_drive_voltage = 1./15

# APD counter integration time (ms)
ctr_time_ms = 1000
ctr_port = 'pfi0'

#######################
# instruments
attoCtrl = mscan.AttocubeNI (chX = '/Weetabix/ao0', chY = '/Weetabix/ao1')
apdCtrl = mdet.APDCounterCtrl (ctr_port = ctr_port,
                         work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                         debug = True)
apdCtrl.set_integration_time_ms(ctr_time_ms)

d = datetime.datetime.now()
#voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
#realPosFilePath = os.path.join(realPosDirectory, 'realPos_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner = attoCtrl, detectors = [apdCtrl])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
#XYscan.restore_back_to_zero()
XYscan.run_scan()
XYscan.save_to_npz('C:/Users/ted/Desktop/measurements/scan1')
#XYscan.save_to_hdf5(file_name=r'C:\Users\ted\Desktop\measurements\test5.hdf5')
#XYscan.plot_counts()


