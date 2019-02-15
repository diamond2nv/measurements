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

delayBetweenPoints = 1.5
delayBetweenRows = 0.

xLims = (0, 30)  # (0, 5)
xStep = 0.2

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'

#######################
# instruments

#psuCtrl = mscan.Keithley2220(VISA_address=r'GPIB0::10::INSTR', channels=[1])


##psuCtrl = mscan.Keithley2220_neg_pos(VISA_address=r'GPIB0::10::INSTR', ch_neg=1, ch_pos=2)
psuCtrl = mscan.Keithley2220_negpos(VISA_address=r'GPIB0::10::INSTR', ch_neg=1, ch_pos=2)
psuCtrl.set_smooth_delay(0.5)

spectroCtrl = mdet.ActonNICtrl(sender_port="/Weetabix/port2/line0",
                               receiver_port="/Weetabix/port2/line4")
multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::13::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'LED4_botGND_topGreenWhite_amp6_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
#volts_scan = mapper.XYScan(scanner_axes=[psuCtrl[0]], detectors=[spectroCtrl, multimeterCtrl])

volts_scan = mapper.XYScan(scanner_axes=[psuCtrl[0]], detectors=[multimeterCtrl])

volts_scan.set_range(xLims=xLims, xStep=xStep)
volts_scan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#volts_scan.set_back_to_zero()

volts_scan.run_scan()

volts_scan.save_to_txt(voltsFilePath, array=volts_scan.counts)

