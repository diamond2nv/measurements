# -*- coding: utf-8 -*-
# @Author: raphaelproux
# @Date:   2018-04-13 00:17:15
# @Last Modified by:   raphaelproux
# @Last Modified time: 2018-04-13 00:26:50

import time
import datetime
import os.path
import sys
from measurements.libs import mapper_scanners as mscan #, mapper_detectors as mdet
from measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
# reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 1
delayBetweenRows = 0.5

xLims = (0, 3)
xStep = 1

yLims = (0, 3)
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
attoCtrl = mscan.TestScanner()

d = datetime.datetime.now()
#voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
#realPosFilePath = os.path.join(realPosDirectory, 'realPos_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYScan(scanner_axes=attoCtrl)
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.restore_back_to_zero()
XYscan.run_scan()
XYscan.save_to_npz(r'C:\Users\QPL\Desktop\temp_measurements')
#XYscan.save_to_hdf5(file_name=r