# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 12:30:11 2018

@author: QPL
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

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'
# APD counter integration time (ms)
ctr_time_ms = 200
ctr_port1 = 'pfi0'

#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL6::INSTR', chX=5, chY=4)
apdCtrl1 = mdet.APDCounterCtrl (ctr_port = ctr_port1,
                         work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                         debug = True)
apdCtrl1.set_integration_time_ms(ctr_time_ms)


x0 = 62
y0 = 84
XYopt = mapper.XYOptimizer(scanner_axes=attoCtrl, detectors=[apdCtrl1])
XYopt.set_scan_range (scan_range=8, scan_step=1)
XYopt.set_delays(between_points=0.3, between_rows=0.3)
XYopt.initialize(x0=x0, y0=y0)
XYopt.run_optimizer (close_instruments=True, silence_errors = False)
#XYopt.run_optimizer (close_instruments=False, silence_errors = False)
#XYopt.run_optimizer (close_instruments=False, silence_errors = False)
#XYopt.run_optimizer (close_instruments=True, silence_errors = False)


