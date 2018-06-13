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

xLims = (56, 100)  # (10, 100)
xStep = 2
yLims = (26, 86)  # (10, 140)
yStep = 2

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'
# APD counter integration time (ms)
ctr_time_ms = 1000
ctr_port1 = 'pfi0'
ctr_port2 = 'pfi1'

#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL6::INSTR', chX=5, chY=4)
apdCtrl1 = mdet.APDCounterCtrl (ctr_port = ctr_port1,
                         work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                         debug = True)
apdCtrl1.set_integration_time_ms(ctr_time_ms)
apdCtrl2 = mdet.APDCounterCtrl (ctr_port = ctr_port2,
                         work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                         debug = True)
apdCtrl2.set_integration_time_ms(ctr_time_ms)


d = datetime.datetime.now()

# Scanning program
XYscan = mapper.XYScan(scanner_axes=attoCtrl, detectors=[apdCtrl1, apdCtrl2]) #voltmeterCtrl])
XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
XYscan.run_scan()
XYscan.save_to_npz('C:/Users/QPL/Desktop/APD_data')

#XYscan.save_to_txt(voltsFilePath, array=XYscan.counts[1], flatten=True)