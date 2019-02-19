# -*- coding: utf-8 -*-
"""
Created on Tue Feb 12 15:11:00 2019

@author: QPL
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato

Voltage sweep with the Keithley power supply while measuring spectra with the Acton spectrometer
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

delayBetweenPoints = 1.5
delayBetweenRows = 0.

xLims = (0, 9)  # (0, 5)
xStep = 0.1

voltsDirectory = r'C:\Users\QPL\Desktop\temp_measurements'


spectroCtrl = mdet.ActonNICtrl(sender_port="/Weetabix/port2/line0",
                               receiver_port="/Weetabix/port2/line4")
#multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::13::INSTR')

magnetCtrl = mscan.MagnetAttocube(address=r'ASRL22::INSTR', tolerance = 0.001, nr_tolerance_reps = 5,
                                   sweep_to_zero_at_end = True)

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'LED4_botGND_topGreenWhite_amp6_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
#volts_scan = mapper.XYScan(scanner_axes=[psuCtrl[0]], detectors=[spectroCtrl, multimeterCtrl])

magnet_scan = mapper.XYScan(scanner_axes=magnetCtrl, detectors=[spectroCtrl])

magnet_scan.set_range(xLims=xLims, xStep=xStep)
magnet_scan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
magnet_scan.set_back_to_zero()

magnet_scan.run_scan(silence_errors = False, do_move_smooth = False)


