# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato

Voltage sweep with the Keithley power supply while measuring spectra with the Acton spectrometer
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

delayBetweenPoints = 1
delayBetweenRows = 0.

xLims = (0, 10)  # (10, 100)
xStep = 0.25

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments
psuCtrl = mscan.KeithleyPSU(VISA_address=r'GPIB0::10::INSTR', channel=1)
spectroCtrl = mdet.ActonLockinCtrl(lockinVisaAddress=r"GPIB0::14::INSTR")
voltmeterCtrl = mdet.VoltmeterCtrl(VISA_address=r'GPIB0::22::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
volts_scan = mapper.XYScan(scanner=psuCtrl, detectors=[spectroCtrl, voltmeterCtrl])
volts_scan.set_range(xLims=xLims, xStep=xStep)
volts_scan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.set_back_to_zero()
volts_scan.run_scan()

volts_scan.save_volts(volts_scan.counts[1], voltsFilePath)

