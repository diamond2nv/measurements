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
from measurements.libs import mapper_detectors as mdet
from  measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mdet)

# APD counter integration time (ms)
ctr_time_ms = 1000
ctr_port = 'pfi0'

#######################
# instruments
apdCtrl = mdet.APDCounterCtrl (ctr_port = ctr_port,
                         work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                         debug = True)
apdCtrl.set_integration_time_ms(ctr_time_ms)

d = datetime.datetime.now()
#voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
#realPosFilePath = os.path.join(realPosDirectory, 'realPos_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

apdCtrl.initialize()


for i in range(0, 50):
    c = apdCtrl.readout()


apdCtrl.close()

